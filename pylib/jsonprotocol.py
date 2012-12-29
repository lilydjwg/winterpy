# vim:fileencoding=utf-8

try:
  import ujson as json
except ImportError:
  import json
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

def fromjson(s):
  return json.loads(s)

def tojson(d):
  return json.dumps(d, ensure_ascii=False)

def write_response(sock, s):
  if isinstance(s, dict):
    s = tojson(s)
  if isinstance(s, str):
    s = s.encode('utf-8')
  sock.sendall(pack_netint(len(s)) + s)

def read_response(sock):
  r = recvbytes(sock, 4)
  if not r:
    return

  length = parse_netint(r)
  data = recvbytes(sock, length)
  if data is None:
    raise Exception('client disappeared suddenly')
  return fromjson(data)

