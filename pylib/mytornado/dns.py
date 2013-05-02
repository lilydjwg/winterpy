# vim:fileencoding=utf-8

import socket
from functools import partial

import tornado.ioloop

from mydns import TYPE, Record, mkquery

def query_via_udp(name, callback, type=TYPE.A, server='127.0.0.1', port=53, *, sock=None, ioloop=None):
  q = mkquery((name, type)).pack()
  if sock is None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(q, (server, port))

  if ioloop is None:
    ioloop = tornado.ioloop.IOLoop.instance()
  ioloop.add_handler(sock.fileno(),
                     partial(_recv_dns_msg, callback, ioloop, sock),
                     ioloop.READ)

def _recv_dns_msg(callback, ioloop, sock, fd, events):
  ret = Record.unpack(sock.recvfrom(1024)[0])
  ioloop.remove_handler(fd)
  callback(ret)

def test():
  import sys
  n = len(sys.argv) - 1
  ioloop = tornado.ioloop.IOLoop.instance()

  def callback(ret):
    nonlocal n
    print(ret.ans)
    n -= 1
    if n == 0:
      ioloop.stop()

  for i in sys.argv[1:]:
    query_via_udp(i, callback)
  ioloop.start()

if __name__ == '__main__':
  test()
