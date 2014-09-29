import fcntl
import os
import re
from select import select
import signal
import sys
import termios
import tty

class Expect:
  buffer = b''
  encoding = sys.getdefaultencoding()

  def __init__(self):
    self.master, self.slave = os.openpty()
    self._old_winch = signal.signal(signal.SIGWINCH, self._size_changed)
    self._size_changed()
    try:
      os.set_inheritable(self.slave, True)
    except AttributeError:
      pass

  def spawn(self, cmd, *, executable=None):
    if executable is None:
      executable = cmd[0]

    pid = os.fork()
    if pid == 0:
      slave = self.slave
      os.dup2(slave, 0)
      os.dup2(slave, 1)
      os.dup2(slave, 2)
      os.close(slave)
      os.execvp(executable, cmd)
    elif pid > 0:
      return
    else:
      raise RuntimeError('os.fork() return negative value?')

  def expect_line(self, regex):
    if isinstance(regex, str):
      regex = regex.encode(self.encoding)
    if isinstance(regex, bytes):
      regex = re.compile(regex)
    if not isinstance(getattr(regex, 'pattern', b''), bytes):
      raise TypeError('regex must be one of type str, bytes or regex of bytes')

    fd = self.master
    outfd = sys.stdout.fileno()
    buf = self.buffer
    try:
      while True:
        if buf:
          data = buf
        else:
          data = os.read(fd, 4096)
          os.write(outfd, data)
        data = data.split(b'\n', 1)
        if len(data) == 2:
          data, buf = data
        else:
          data = data[0]
        if regex.search(data):
          return
    finally:
      self.buffer = buf

  def _read_write(self, data):
    fd = self.master
    outfd = sys.stdout.fileno()
    to_write = len(data)
    while to_write:
      try:
        r, w, e = select([fd], [fd], [])
        if r:
          data = os.read(fd, 4096)
          os.write(outfd, data)
        if w:
          written = os.write(fd, data)
          data = data[written:]
          to_write -= written
      except InterruptedError:
        continue

  def send(self, data):
    if isinstance(data, str):
      data = data.encode(self.encoding)
    self._read_write(data)

  def interact(self):
    pfd = sys.stdin.fileno()
    cfd = self.master
    outfd = sys.stdout.fileno()
    old = termios.tcgetattr(pfd)
    old_signal = signal.signal(signal.SIGCHLD, self._interact_leave)

    tty.setraw(pfd)
    try:
      while True:
        try:
          r, w, e = select([pfd, cfd], [], [])
          for fd in r:
            data = os.read(fd, 4096)
            other = outfd if fd == cfd else cfd
            os.write(other, data)
        except InterruptedError:
          continue
    except ChildProcessError:
      pass
    finally:
      termios.tcsetattr(pfd, termios.TCSAFLUSH, old)
      signal.signal(signal.SIGCHLD, old_signal)

  def _interact_leave(self, signum, sigframe):
    while os.waitid(os.P_ALL, 0, os.WEXITED | os.WNOHANG) is not None:
      pass

  def _size_changed(self, signum=0, sigframe=None):
    size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, '1234')
    fcntl.ioctl(self.master, termios.TIOCSWINSZ, size)

  def __del__(self):
    if self._old_winch:
      signal.signal(signal.SIGWINCH, self._old_winch)
