import struct

def parse_netint(b):
  return struct.unpack('!I', b)[0]

def pack_netint(i):
  return struct.pack('!I', i)

def recvbytes(sock, length):
  got = 0
  data = []
  while got < length:
    r = sock.recv(length - got)
    if not r:
      return
    got += len(r)
    data.append(r)
  return b''.join(data)

class LengthPrefixedMessenger(object):
  def __init__(self, sock):
    self.sock = sock

  def send(self, s):
    self.sock.sendall(pack_netint(len(s)) + s)

  def recv(self):
    sock = self.sock
    r = recvbytes(sock, 4)
    if not r:
      raise EOFError

    length = parse_netint(r)
    data = recvbytes(sock, length)
    if data is None:
      raise EOFError('client disappeared suddenly')
    return data

  def __getattr__(self, name):
    return getattr(self.sock, name)

  def accept(self):
    s, addr = self.sock.accept()
    s = self.__class__(s)
    return s, addr

  def close(self):
      self.sock.close()
      # discard results to closed socket
      self.send = lambda x: None
