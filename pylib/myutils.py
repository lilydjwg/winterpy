'''
一些常用短小的函数/类
'''

import os, sys
import datetime
from functools import lru_cache, wraps
import logging
import time

def path_import(path):
  '''指定路径来 import'''
  d, f = os.path.split(path)
  if d not in sys.path:
    sys.path[0:0] = [d]
    ret = __import__(os.path.splitext(f)[0])
    del sys.path[0]
    return ret

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

def getchar(prompt, hidden=False, end='\n'):
  '''读取一个字符'''
  import termios
  sys.stdout.write(prompt)
  sys.stdout.flush()
  fd = sys.stdin.fileno()

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
      ch = os.read(fd, 7)
    finally:
      termios.tcsetattr(fd, termios.TCSAFLUSH, old)
  else:
    ch = os.read(fd, 7)

  sys.stdout.write(end)
  return(ch.decode())

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
def enable_pretty_logging(level=logging.DEBUG):
  logger = logging.getLogger()
  h = logging.StreamHandler()
  formatter = logging.Formatter('%(asctime)s:%(levelname)-7s:%(name)-12s:%(message)s')
  try:
    import curses
    color = False
    curses.setupterm()
    if curses.tigetnum("colors") > 0:
      color = True
    formatter = TornadoLogFormatter(color=color)
  except:
    import traceback
    traceback.print_exc()
  finally:
    h.setLevel(level)
    h.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(h)

class TornadoLogFormatter(logging.Formatter):
  def __init__(self, color, *args, **kwargs):
    super().__init__(self, *args, **kwargs)
    self._color = color
    if color:
      import curses
      curses.setupterm()
      if sys.hexversion < 50463728:
        fg_color = str(curses.tigetstr("setaf") or
                   curses.tigetstr("setf") or "", "ascii")
      else:
        fg_color = curses.tigetstr("setaf") or curses.tigetstr("setf") or b""
      self._colors = {
        logging.DEBUG: str(curses.tparm(fg_color, 4), # Blue
                     "ascii"),
        logging.INFO: str(curses.tparm(fg_color, 2), # Green
                    "ascii"),
        logging.WARNING: str(curses.tparm(fg_color, 3), # Yellow
                     "ascii"),
        logging.ERROR: str(curses.tparm(fg_color, 1), # Red
                     "ascii"),
      }
      self._normal = str(curses.tigetstr("sgr0"), "ascii")

  def format(self, record):
    try:
      record.message = record.getMessage()
    except Exception as e:
      record.message = "Bad message (%r): %r" % (e, record.__dict__)
    record.asctime = time.strftime(
      "%m-%d %H:%M:%S", self.converter(record.created))
    record.asctime += '.%03d' % ((record.created % 1) * 1000)
    prefix = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]' % \
      record.__dict__
    if self._color:
      prefix = (self._colors.get(record.levelno, self._normal) +
            prefix + self._normal)
    formatted = prefix + " " + record.message
    if record.exc_info:
      if not record.exc_text:
        record.exc_text = self.formatException(record.exc_info)
    if record.exc_text:
      formatted = formatted.rstrip() + "\n" + record.exc_text
    return formatted.replace("\n", "\n    ")

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

