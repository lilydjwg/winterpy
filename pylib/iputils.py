import re
from ipaddress import IPv4Network, IPv4Address

def range2network(a, b):
  ipa = IPv4Address(a)
  ipb = IPv4Address(b)
  host_length = (int(ipa) ^ int(ipb)).bit_length()
  return '%s/%d' % (a, 32-host_length)

def network2range(n):
  n = IPv4Network(n)
  return str(n.network_address), str(n.broadcast_address)

ipv4_re = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b')

if __name__ == '__main__':
  import sys
  for i in sys.argv[1:]:
    if '/' in i:
      a, b = network2range(i)
      print(a, '-', b)
    else:
      a, *_, b = i.split()
      print(range2network(a, b))

