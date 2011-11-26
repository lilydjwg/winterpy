'''
PID 管理，在 with 语句中使用，控制进程只有一个在运行，否则抛出 AlreadyRun 异常
'''

import os
import sys
import time

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

class Daemonized(PIDFile):
  '''
  除了 pid 文件外，同时处理以下事务：
  - fork & wait
  - 更改当前目录到 /
  - 重定向标准输入/输出/错误到 /dev/null
  '''
  def __init__(self, pidfile, wait_time=0.5):
    '''
    wait_time: 父进程退出前等待时间，默认 0.5 秒
    '''
    pid = os.fork()
    if pid:
      time.sleep(0.5) # check if error ocurrs in child process
      res = os.waitpid(pid, os.WNOHANG)
      os._exit(res[1] != 0)

    super().__init__(pidfile)
    os.chdir('/')
    fd = os.open('/dev/null', os.O_RDWR)
    os.dup2(fd, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)

class AlreadyRun(Exception):
  def __init__(self, pid):
    self.pid = pid
  def __repr__(self):
    return "Process with pid %d is already running" % self.pid

