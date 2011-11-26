'''利用 poll() 与子进程交互'''

import subprocess
import select
import errno
import os

PIPE = subprocess.PIPE

class Subprocess(subprocess.Popen):
  '''与子进程交互式通信

  decode 默认为 True，即自动解码。如果调用 input() 时给出的是
  bytes，则此值自动置为 False。
  bytesAtatime 是每次读取输出的大小，默认为 1024

  polls[fd] 是 select.poll 对象
  '''
  decode = True
  bytesAtatime = 1024

  def input(self, msg):
    '''将 msg 送到子进程的 stdin

    如果写操作将阻塞，抛出 IOError，errno 为 EAGAIN（EWOULDBLOCK）
    如果 stdin 未指定为 PIPE，抛出 AttributeError
    '''
    if self.stdin is None:
      raise AttributeError('stdin 不是 pipe')

    if not hasattr(self, 'polls'):
      self.polls = {}
    fd = self.stdin.fileno()
    if fd not in self.polls:
      self.polls[fd] = select.poll()
      self.polls[fd].register(fd, select.POLLOUT)

    r = self.polls[fd].poll(5)
    if not r:
      raise IOError(errno.EWOULDBLOCK, 'writing would block')

    if isinstance(msg, str):
      msg = msg.encode()
      self.decode = True
    else:
      self.decode = False

    self.stdin.write(msg)
    self.stdin.flush()

  def poll(self, fd, timeout):
    '''从文件描述符 fd 中读取尽可能多的字符，返回类型由 decode 属性决定'''
    ret = b''

    if not hasattr(self, 'polls'):
      self.polls = {}
    if fd not in self.polls:
      self.polls[fd] = select.poll()
      self.polls[fd].register(fd, select.POLLIN)

    fd = self.polls[fd].poll(timeout)
    while fd:
      r = os.read(fd[0][0], self.bytesAtatime)
      ret += r
      if len(r) < self.bytesAtatime:
        break

    if self.decode:
      return ret.decode()
    else:
      return ret

  def output(self, timeout=0.05):
    '''如果指定了 stdout=PIPE，则返回 stdout 输出，否则抛出 AttributeError 异常
    timeout 单位为秒'''
    if isinstance(timeout, int):
      timeout *= 1000
    if self.stdout is not None:
      return self.poll(self.stdout.fileno(), timeout=timeout)
    else:
      raise AttributeError('stdout 不是 pipe')

  def error(self, timeout=0.05):
    '''如果指定了 stderr=PIPE，则返回 stderr 输出，否则抛出 AttributeError 异常'''
    if self.stderr is not None:
      return self.poll(self.stderr.fileno(), timeout=timeout)
    else:
      raise AttributeError('stderr 不是 pipe')
