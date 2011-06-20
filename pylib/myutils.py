#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
一些常用短小的函数/类
'''

import os, sys

def path_import(path):
  '''指定路径来 import'''
  d, f = os.path.split(path)
  if d not in sys.path:
    sys.path[0:0] = [d]
    ret = __import__(os.path.splitext(f)[0])
    del sys.path[0]
    return ret

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
def restart_when_done(func, max_times, args=(), kwargs={}, secs=60):
  '''
  在函数退出后重新运行之，直到在 secs 秒（默认一分钟）时间内达到 max_times 次退出
  '''
  import time
  from collections import deque
  dq = deque(maxlen=max_times)

  dq.append(time.time())
  func(*args, **kwargs)
  while len(dq) < max_times or time.time() - dq[0] > secs:
    dq.append(time.time())
    func(*args, **kwargs)
