# Copyright (c) 2013-2021 lilydjwg. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#     3. Neither the name of the copyright holder nor the names of its
#        contributors may be used to endorse or promote products derived from
#        this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import socket as _socket
import time
import struct

'''
Utilities for ICMP socket.

For the socket usage: https://lkml.org/lkml/2011/5/10/389
For the packet structure: https://bitbucket.org/delroth/python-ping

BSD 3-Clause "New" or "Revised" License.
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

async def aping(s, address, seq=1):
  import asyncio
  s.sendto(pack_packet_with_time(seq), (address, 0))
  loop = asyncio.get_running_loop()

  while True:
    fu = asyncio.Future()
    loop.add_reader(s, fu.set_result, None)
    try:
      await fu
    finally:
      loop.remove_reader(s)

    t = None
    while True:
      try:
        packet, peer = s.recvfrom(1024)
        r_seq, r_t = parse_packet_with_time(packet)
        if r_seq == seq:
          t = r_t
      except BlockingIOError:
        break

    if t:
      break
    # else retry read

  return time.time() - t

async def amain(address):
  import asyncio
  address = _socket.gethostbyname(address)
  s = socket()
  s.setblocking(False)
  seq = 0
  while True:
    try:
      seq += 1
      t = await asyncio.wait_for(aping(s, address, seq), 2)
      print('%9.3fms' % (t * 1000))
      await asyncio.sleep(1 - t)
    except TimeoutError:
      print('timed out.')
    except BlockingIOError:
      print('EWOULDBLOCK')
    except asyncio.CancelledError:
      print()
      break

def main():
  import sys
  if len(sys.argv) != 2:
    sys.exit('where to ping?')
  t = ping(sys.argv[1])
  print('%9.3fms.' % (t * 1000))

if __name__ == '__main__':
  main()
  # import asyncio, sys
  # asyncio.run(amain(sys.argv[1]))
