'''
PID 管理，在 with 语句中使用，控制进程只有一个在运行，否则抛出 AlreadyRun 异常
'''

import os
import sys
import time
import signal

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

def wait_and_exit(pid):
  res = os.waitpid(pid, 0)[1]
  status = res & 0x7f
  if status == 0:
    status = (res & 0xff00) >> 8
  sys.stdout.flush()
  os._exit(status)

def _got_sgiusr2(signum, sigframe):
  os._exit(0)

class Daemonized(PIDFile):
  '''daemonize the process and then write its pid to file
  * fork
    * chdir("/")
    * setsid
    * fork
      * close fds
      * do_work
    * killed by SIGUSR2
    * _exit
  * waitpid
  * _exit

  This procedure is borrowed from MongoDB.
  '''
  def __init__(self, pidfile):
    pid = os.fork()
    if pid:
      wait_and_exit(pid)

    os.chdir('/')
    os.setsid()
    leader = os.getpid()
    pid_2 = os.fork()
    if pid_2:
      signal.signal(signal.SIGUSR2, _got_sgiusr2)
      wait_and_exit(pid_2)

    super().__init__(pidfile)
    fd = os.open('/dev/null', os.O_RDWR)
    os.dup2(fd, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    os.close(fd)
    os.kill(leader, signal.SIGUSR2)

class AlreadyRun(Exception):
  def __init__(self, pid):
    self.pid = pid
  def __repr__(self):
    return "Process with pid %d is already running" % self.pid

