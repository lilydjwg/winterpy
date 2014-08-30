from ipaddress import IPv4Network, IPv4Address

def range2network(a, b):
  ipa = IPv4Address(a)
  ipb = IPv4Address(b)
  host_length = (int(ipa) ^ int(ipb)).bit_length()
  return '%s/%d' % (a, 32-host_length)

def network2range(n):
  n = IPv4Network(n)
  return str(n.network_address), str(n.broadcast_address)

if __name__ == '__main__':
  import sys
  for i in sys.argv[1:]:
    if '/' in i:
      a, b = network2range(i)
      print(a, '-', b)
    else:
      a, *_, b = i.split()
      print(range2network(a, b))

