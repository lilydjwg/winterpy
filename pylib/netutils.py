import socket
import fcntl
import struct

def get_my_ip(ifname):
  ifname = ifname.encode('ascii')
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # 0x8915 是 SIOCGIFADDR
  try:
    result = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24]
  except OSError as e:
    if e.errno == 99: # Cannot assign requested address
      return None
    else:
      raise

  ip = socket.inet_ntoa(result)
  return ip

def get_interface_names():
  ret = []
  with open('/proc/net/dev') as f:
    for line in f:
      first = line.split(None, 1)[0]
      if first.endswith(':'):
        ret.append(first[:-1])
  return ret
