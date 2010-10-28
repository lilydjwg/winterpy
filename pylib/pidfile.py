#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
一个 context manager，控制进程只有一个在运行，否则抛出 AlreadyRun 异常

2010年9月4日
'''

import os

class PIDFile:
  def __init__(self, pidfile):
    self.pidfile = pidfile
    try:
      pid = int(open(pidfile).read())
    except (IOError, ValueError):
      open(pidfile, 'w').write(str(os.getpid()))
      return
    else:
      try:
        os.kill(pid, 0)
      except OSError:
        open(pidfile, 'w').write(str(os.getpid()))
      else:
        raise AlreadyRun(pid)

  def __enter__(self):
    pass

  def __exit__(self, exc_type, exc_value, traceback):
    os.unlink(self.pidfile)

class AlreadyRun(Exception):
  def __init__(self, pid):
    self.pid = pid
  def __repr__(self):
    return "Process with pid %d is already running" % self.pid

