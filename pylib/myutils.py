'''
一些常用短小的函数/类
'''

import os, sys
import datetime
from functools import lru_cache, wraps
import logging
try:
  import ipaddress
except ImportError:
  # Python 3.2-
  ipaddress = None
import contextlib
import signal
import hashlib

from nicelogger import enable_pretty_logging

def safe_overwrite(fname, data, *, method='write', mode='w', encoding=None):
  # FIXME: directory has no read perm
  # FIXME: symlinks and hard links
  tmpname = fname + '.tmp'
  # if not using "with", write can fail without exception
  with open(tmpname, mode, encoding=encoding) as f:
    getattr(f, method)(data)
  # if the above write failed (because disk is full etc), the old data should be kept
  os.rename(tmpname, fname)

def filesize(size):
  '''将 数字 转化为 xxKiB 的形式'''
  units = 'KMGT'
  left = abs(size)
  unit = -1
  while left > 1100 and unit < 3:
    left = left / 1024
    unit += 1
  if unit == -1:
    return '%dB' % size
  else:
    if size < 0:
      left = -left
    return '%.1f%siB' % (left, units[unit])

class FileSize(int):
  def __str__(self):
    return filesize(self).rstrip('iB')

def humantime(t):
  '''seconds -> XhYmZs'''
  units = 'hms'
  m, s = divmod(t, 60)
  h, m = divmod(m, 60)
  ret = ''
  if h:
    ret += '%dh' % h
  if m:
    ret += '%dm' % m
  if s:
    ret += '%ds' % s
  return ret

def input_t(timeout, prompt=''):
  '''带有超时的输入，使用 select() 实现

  超时返回 None'''
  from select import select

  # 也可以用多进程/signal 实现
  # 但 signal 不能在非主线程中调用
  sys.stdout.write(prompt)
  sys.stdout.flush()
  if select([sys.stdin.fileno()], [], [], timeout)[0]:
    return input()

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

  def _read():
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

def restart_if_failed(func, max_tries, args=(), kwargs={}, secs=60, sleep=None):
  '''
  re-run when some exception happens, until `max_tries` in `secs`
  '''
  import time
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

  old_hdl = signal.signal(signal.SIGALRM, timed_out)
  old_itimer = signal.setitimer(signal.ITIMER_REAL, timeout, 0)
  yield
  signal.setitimer(signal.ITIMER_REAL, *old_itimer)
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
  if ipaddress is None:
    return False

  ip = ipaddress.ip_address(ip)
  return ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_link_local

@contextlib.contextmanager
def at_dir(d):
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
      d = f.read(8192)
      if not d:
        break
      m.update(d)
  return m.hexdigest()

def md5(s, encoding='utf-8'):
  m = hashlib.md5()
  m.update(s.encode(encoding))
  return m.hexdigest()
