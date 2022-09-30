from __future__ import annotations

import socket
import fcntl
import struct
from typing import Optional

def get_my_ip(ifname: str) -> str:
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

def get_interface_names() -> list[str]:
  ret = []
  with open('/proc/net/dev') as f:
    for line in f:
      first = line.split(None, 1)[0]
      if first.endswith(':'):
        ret.append(first[:-1])
  return ret

def get_gateway_ipv4() -> Optional[str, str]:
  with open('/proc/net/route') as f:
    for l in f:
      parts = l.split()
      if parts[1] == '00000000':
        iface = parts[0]
        n = socket.ntohl(int(parts[2], 16))
        gateway = socket.inet_ntoa(n.to_bytes(4, 'big'))
        return iface, gateway

  return None, None

AKAMAI_NS_SERVERS = ['193.108.91.133', '184.85.248.64', '2.16.130.66']
def get_self_ip_akamai(server):
  import subprocess
  lines = subprocess.check_output(
    ['dig', 'whoami.ipv4.akahelp.net', 'TXT', f'@{server}', '+short'],
    stderr = subprocess.DEVNULL,
    text = True,
  ).splitlines()

  for line in lines:
    if line.startswith(';;'):
      continue
    if line.startswith('"ns" '):
      return line.split()[-1].strip('"')

GOOGLE_NS_SERVERS = ['216.239.32.10', '216.239.34.10']
def get_self_ip_google(server):
  import subprocess
  lines = subprocess.check_output(
    ['dig', 'o-o.myaddr.l.google.com', 'TXT', f'@{server}', '+short'],
    stderr = subprocess.DEVNULL,
    text = True,
  ).splitlines()

  for line in lines:
    if line.startswith(';;'):
      continue
    if line.startswith('"'):
      return line.strip('"')

