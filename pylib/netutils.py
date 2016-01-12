import socket
import fcntl
import struct

def get_my_ip(ifname):
  ifname = ifname.encode('ascii')
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  # 0x8915 是 SIOCGIFADDR
  ip = socket.inet_ntoa(
    fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])
  return ip

