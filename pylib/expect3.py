'''
python 版的 expect

2010年8月5日
'''

try:
  import sys, os
  import re
  import pty
  import tty
  import termios
  import struct
  import fcntl
  import resource
  import select
  import signal
  import time
except ImportError:
  print('''Someting went wrong while importing modules.
Is this a Unix-like system?''', file=sys.stderr)

class spawn:
  def __init__(self, command, executable=None, timeout=30, maxread=2000, searchwindowsize=None, logfile=None, timefile=None, cwd=None, env=None, winsize=None):
    '''
    command: list，要执行的命令
    logfile: file, 记录输出的文件
    winsize: None, 自动设置终端大小
    '''
    if executable is None:
      executable = command[0]

    self.fd = sys.stdout.fileno()

    pid, fd = pty.fork()
    if pid == 0: # 子进程
      self.parent = False

      # Do not allow child to inherit open file descriptors from parent.
      max_fd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
      os.closerange(3, max_fd)
      if cwd is not None:
        os.chdir(cwd)
      if env is None:
        os.execvp(executable, command)
      else:
        os.execvpe(executable, command, env)
    else:
      self.parent = True
      self.ptyfd = fd
      self.readbuffer = b''

      if winsize is None:
        self.updatewinsize()
        def sigwinch_passthrough(sig, data):
          self.updatewinsize()
        signal.signal(signal.SIGWINCH, sigwinch_passthrough)
      else:
        self.setwinsize(*winsize)

      self.timeout = timeout
      self.maxread = maxread
      self.searchwindowsize = searchwindowsize
      self.logfile = logfile
      self.timefile = timefile
      if timefile:
        self.lasttime = time.time()

  def fileno(self):
    return self.ptyfd

  def expect(self, what):
    if isinstance(what, str):
      what = what.encode()

    if re.search(what, self.readbuffer):
      return

    fd = self.ptyfd
    while True:
      self._read()
      if re.search(what, self.readbuffer):
        break

    self.readbuffer = b''

  def _read(self):
    try:
      s = os.read(self.ptyfd, 1024)
    except OSError as e:
      if e.errno == 5:
        raise EOFError
      else:
        raise

    self.readbuffer += s
    if self.logfile:
      self.logfile.write(s)
      self.logfile.flush()
    if self.timefile:
      t = time.time()
      self.timefile.write('%.6f %d\n' % (t-self.lasttime, len(s)))
      self.timefile.flush()
      self.lasttime = t

  def read(self):
    '''read something to self.readbuffer'''
    rd, wd, ed = select.select([self.ptyfd], [], [], 0)
    while rd:
      self._read()
      rd, wd, ed = select.select([self.ptyfd], [], [], 0)

  def send(self, what):
    if isinstance(what, str):
      what = what.encode()
    os.write(self.ptyfd, what)

  def sendline(self, what):
    if isinstance(what, str):
      what = what.encode()
    what += b'\r'
    self.send(what)

  def interact(self):
    os.write(self.fd, self.readbuffer)
    old = termios.tcgetattr(self.fd)
    new = termios.tcgetattr(self.fd)
    new[3] = new[3] & ~termios.ECHO
    try:
      tty.setraw(self.fd)
      while True:
        try:
          rd, wd, ed = select.select([self.ptyfd, self.fd], [], [])
        except select.error as e:
          if e.args[0] == 4:
            continue
          else:
            raise
        for i in rd:
          if i == self.ptyfd:
            s = os.read(i, 1024)
            os.write(self.fd, s)
          elif i == self.fd:
            s = os.read(i, 1024)
            os.write(self.ptyfd, s)
    except OSError as e:
      if e.errno == 5:
        # 使用 print() 会导致下一个 Python 提示符位置不对
        os.write(self.fd, '已结束。\r\n'.encode())
      else:
        raise
    finally:
      termios.tcsetattr(self.fd, termios.TCSADRAIN, old)

  def setwinsize(self, columns, lines):
    s = struct.pack('HHHH', lines, columns, 0, 0)
    fcntl.ioctl(self.ptyfd, termios.TIOCSWINSZ, s)

  def updatewinsize(self):
    '''update winsize to the same as the parent'''
    s = struct.pack("HHHH", 0, 0, 0, 0)
    a = struct.unpack('hhhh', fcntl.ioctl(self.fd, termios.TIOCGWINSZ, s))
    self.setwinsize(a[1], a[0])

