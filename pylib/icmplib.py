import socket as _socket
import time
import struct

'''
Utilities for ICMP socket.

For the socket usage: https://lkml.org/lkml/2011/5/10/389
For the packet structure: https://bitbucket.org/delroth/python-ping
'''

ICMP_ECHO_REQUEST = 8
_d_size = struct.calcsize('d')

def pack_packet(seq, payload):
  # Header is type (8), code (8), checksum (16), id (16), sequence (16)
  # The checksum is always recomputed by the kernel, and the id is the port number
  header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, 0, seq)
  return header + payload

def parse_packet(data):
  type, code, checksum, packet_id, sequence = struct.unpack('bbHHh', data[:8])
  return sequence, data[8:]

def pack_packet_with_time(seq, packetsize=56):
  padding = (packetsize - _d_size) * b'Q'
  timeinfo = struct.pack('d', time.time())
  return pack_packet(seq, timeinfo + padding)

def parse_packet_with_time(data):
  seq, payload = parse_packet(data)
  t = struct.unpack('d', payload[:_d_size])[0]
  return seq, t

def socket():
  return _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM, _socket.IPPROTO_ICMP)

def ping(address):
  address = _socket.gethostbyname(address)
  s = socket()
  s.sendto(pack_packet_with_time(1), (address, 0))
  packet, peer = s.recvfrom(1024)
  _, t = parse_packet_with_time(packet)
  return time.time() - t

def main():
  import sys
  if len(sys.argv) != 2:
    sys.exit('where to ping?')
  t = ping(sys.argv[1])
  print('%9.3fms.' % (t * 1000))

if __name__ == '__main__':
  main()
