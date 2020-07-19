from __future__ import annotations

import os, sys
import re
import datetime
import time
from functools import lru_cache, wraps
import logging
import contextlib
import signal
import hashlib
import base64
import fcntl
from typing import Union, Optional, Dict, Any, Generator

logger = logging.getLogger(__name__)

def safe_overwrite(fname: str, data: Union[bytes, str], *,
                   method: str = 'write', mode: str = 'w', encoding: Optional[str] = None) -> None:
  # FIXME: directory has no read perm
  # FIXME: symlinks and hard links
  tmpname = fname + '.tmp'
  # if not using "with", write can fail without exception
  with open(tmpname, mode, encoding=encoding) as f:
    getattr(f, method)(data)
    # see also: https://thunk.org/tytso/blog/2009/03/15/dont-fear-the-fsync/
    f.flush()
    os.fsync(f.fileno())
  # if the above write failed (because disk is full etc), the old data should be kept
  os.rename(tmpname, fname)

UNITS = 'KMGTPEZY'

def filesize(size: int) -> str:
  '''将 数字 转化为 xxKiB 的形式'''
  left: Union[int, float] = abs(size)
  unit = -1
  n = len(UNITS)
  while left > 1100 and unit < n:
    left = left / 1024
    unit += 1
  if unit == -1:
    return '%dB' % size
  else:
    if size < 0:
      left = -left
    return '%.1f%siB' % (left, UNITS[unit])

class FileSize(int):
  def __str__(self) -> str:
    return filesize(self).rstrip('iB')

def parse_filesize(s: str) -> int:
  s1 = s.rstrip('iB')
  if not s1:
    raise ValueError(s)

  last = s1[-1]
  try:
    idx = UNITS.index(last)
  except ValueError:
    return int(s1)

  v = float(s1[:-1]) * 1024 ** (idx+1)
  return int(v)

def humantime(t: int) -> str:
  '''seconds -> XhYmZs'''
  if t < 0:
    sign = '-'
    t = -t
  else:
    sign = ''

  m, s = divmod(t, 60)
  h, m = divmod(m, 60)
  d, h = divmod(h, 24)
  ret = ''
  if d:
    ret += '%dd' % d
  if h:
    ret += '%dh' % h
  if m:
    ret += '%dm' % m
  if s:
    ret += '%ds' % s
  if not ret:
    ret = '0s'
  return sign + ret

def dehumantime(s: str) -> int:
  '''XhYmZs -> seconds'''
  m = re.match(r'(?:(?P<d>\d+)d)?(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?(?:(?P<s>\d+)s)?$', s)
  if m:
    return (
      int(m.group('d') or 0) * 3600 * 24 +
      int(m.group('h') or 0) * 3600 +
      int(m.group('m') or 0) * 60 +
      int(m.group('h') or 0)
    )
  else:
    raise ValueError(s)

def _timed_read(file, timeout):
  from select import select
  if select([file], [], [], timeout)[0]:
    return file.read(1)

def getchar(prompt, hidden=False, end='\n', timeout=None):
  '''读取一个字符'''
  import termios
  sys.stdout.write(prompt)
  sys.stdout.flush()
  fd = sys.stdin.fileno()
  ch: Optional[str]

  def _read() -> Optional[str]:
    ch: Optional[str]
    if timeout is None:
      ch = sys.stdin.read(1)
    else:
      ch = _timed_read(sys.stdin, timeout)
    return ch

  if os.isatty(fd):
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    if hidden:
      new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
    else:
      new[3] = new[3] & ~termios.ICANON
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    try:
      termios.tcsetattr(fd, termios.TCSANOW, new)
      termios.tcsendbreak(fd, 0)
      ch = _read()
    finally:
      termios.tcsetattr(fd, termios.TCSAFLUSH, old)
  else:
    ch = _read()

  sys.stdout.write(end)
  return ch

def loadso(fname):
  '''ctypes.CDLL 的 wrapper，从 sys.path 中搜索文件'''
  from ctypes import CDLL

  for d in sys.path:
    p = os.path.join(d, fname)
    if os.path.exists(p):
      return CDLL(p)
  raise ImportError('%s not found' % fname)

def dofile(path):
  G = {}
  with open(path) as f:
    exec(f.read(), G)
  return G

def restart_if_failed(func, max_tries, args=(), kwargs={}, secs=60, sleep=None):
  '''
  re-run when some exception happens, until `max_tries` in `secs`
  '''
  import traceback
  from collections import deque

  dq = deque(maxlen=max_tries)
  while True:
    dq.append(time.time())
    try:
      func(*args, **kwargs)
    except:
      traceback.print_exc()
      if len(dq) == max_tries and time.time() - dq[0] < secs:
        break
      if sleep is not None:
        time.sleep(sleep)
    else:
      break

def daterange(start, stop=datetime.date.today(), step=datetime.timedelta(days=1)):
  d = start
  while d < stop:
    yield d
    d += step

@lru_cache()
def findfont(fontname):
  from subprocess import check_output
  out = check_output(['fc-match', '-v', fontname]).decode()
  for l in out.split('\n'):
    if l.lstrip().startswith('file:'):
      return l.split('"', 2)[1]

def debugfunc(logger=logging, *, _id=[0]):
  def w(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      myid = _id[0]
      _id[0] += 1
      logger.debug('[func %d] %s(%r, %r)', myid, func.__name__, args, kwargs)
      ret = func(*args, **kwargs)
      logger.debug('[func %d] return: %r', myid, ret)
      return ret
    return wrapper
  return w

@contextlib.contextmanager
def execution_timeout(timeout):
  def timed_out(signum, sigframe):
    raise TimeoutError

  delay, interval = signal.setitimer(signal.ITIMER_REAL, timeout, 0)
  old_hdl = signal.signal(signal.SIGALRM, timed_out)
  now = time.time()
  try:
    yield
  finally:
    # inner timeout must be smaller, or the timer event will be delayed
    if delay:
      elapsed = time.time() - now
      delay = max(delay - elapsed, 0.000001)
    else:
      delay = 0
    signal.setitimer(signal.ITIMER_REAL, delay, interval)
    signal.signal(signal.SIGALRM, old_hdl)

def find_executables(name, path=None):
  '''find all matching executables with specific name in path'''
  if path is None:
    path = os.environ['PATH'].split(os.pathsep)
  elif isinstance(path, str):
    path = path.split(os.pathsep)
  path = [p for p in path if os.path.isdir(p)]

  return [os.path.join(p, f) for p in path for f in os.listdir(p) if f == name]

# The following three are learnt from makepkg
def user_choose(prompt, timeout=None):
  # XXX: hard-coded term characters are ok?
  prompt = '\x1b[1;34m::\x1b[1;37m %s\x1b[0m ' % prompt
  return getchar(prompt, timeout=timeout)

def msg(msg):
  # XXX: hard-coded term characters are ok?
  print('\x1b[1;32m==>\x1b[1;37m %s\x1b[0m' % msg)

def msg2(msg):
  # XXX: hard-coded term characters are ok?
  print('\x1b[1;34m  ->\x1b[1;37m %s\x1b[0m' % msg)

def is_internal_ip(ip):
  import ipaddress
  ip = ipaddress.ip_address(ip)
  return ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_link_local

@contextlib.contextmanager
def at_dir(d: os.PathLike) -> Generator[None, None, None]:
  old_dir = os.getcwd()
  os.chdir(d)
  try:
    yield
  finally:
    os.chdir(old_dir)

def firstExistentPath(paths):
  for p in paths:
    if os.path.exists(p):
      return p

def md5sum_of_file(file):
  with open(file, 'rb') as f:
    m = hashlib.md5()
    while True:
      d = f.read(81920)
      if not d:
        break
      m.update(d)
  return m.hexdigest()

def md5(s, encoding='utf-8'):
  m = hashlib.md5()
  m.update(s.encode(encoding))
  return m.hexdigest()

def base64_encode(s):
  if isinstance(s, str):
    s = s.encode()
  return base64.b64encode(s).decode('ascii')

def lock_file(path: os.PathLike) -> None:
  lock = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
  try:
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:
    logger.warning('Waiting for lock to release...')
    fcntl.flock(lock, fcntl.LOCK_EX)

@contextlib.contextmanager
def file_lock(file):
  lock = os.open(file, os.O_WRONLY | os.O_CREAT, 0o600)
  try:
    fcntl.flock(lock, fcntl.LOCK_EX)
    yield
  finally:
    os.close(lock)

def dict_bytes_to_str(d: Dict[Any, Any]) -> Dict[Any, Any]:
  ret = {}
  for k, v in d.items():
    if isinstance(k, bytes):
      try:
         k = k.decode()
      except UnicodeDecodeError:
        pass

    if isinstance(v, bytes):
      try:
         v = v.decode()
      except UnicodeDecodeError:
        pass
    elif isinstance(v, dict):
      v = dict_bytes_to_str(v)
    elif isinstance(v, list):
      try:
         v = [x.decode() for x in v]
      except UnicodeDecodeError:
        pass

    ret[k] = v

  return ret

def xsel(input=None):
  import subprocess

  if input is None:
    return subprocess.getoutput('xsel')
  else:
    p = subprocess.Popen('xsel', stdin=subprocess.PIPE)
    p.communicate(input.encode())
    return p.wait()
