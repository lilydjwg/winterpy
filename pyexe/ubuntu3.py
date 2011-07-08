#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
Ubuntu 中文论坛加速脚本
依原 cx_freeze 的 py2.6 版重写
'''

import socket
import zlib

import tornado.ioloop
import tornado.web
import tornado.iostream
import tornado.httpclient

class MainHandler(tornado.web.RequestHandler):
  @tornado.web.asynchronous
  def get(self):
    self.handle_requset()

  @tornado.web.asynchronous
  def post(self):
    self.handle_requset()

  def handle_requset(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rcon = tornado.iostream.IOStream(s)
    self.rcon = rcon
    rcon.connect(('cdn.ubuntu.org.cn', 8111), self.send_request)

  def send_request(self):
    req = self.request
    uri = req.uri[req.uri.find('/', 8):]
    data = ['%s %s HTTP/1.0' % (req.method, uri)]
    req.headers['connection'] = 'close'
    for h in req.headers.items():
      data.append('{}: {}'.format(*h))
    data.append('\r\n')
    bdata = '\r\n'.join(data).encode('latin1')
    if req.method == 'POST':
      bdata += req.body
    data = zlib.compress(bdata)
    rcon = self.rcon
    length = '%d\n' % len(data)
    rcon.write(length.encode('ascii'))
    rcon.write(data)
    self._headers_written = True
    rcon.read_bytes(8192, self.on_data)
    rcon.set_close_callback(self.on_close)

  def on_data(self, data):
    self.request.write(data)
    if len(data) == 8192:
      self.rcon.read_bytes(8192, self.on_data)
    else:
      self.finish()

  def on_close(self):
    self.rcon._read_bytes = self.rcon._read_buffer_size
    self.rcon._read_from_buffer()

application = tornado.web.Application([
  (r"/.*", MainHandler),
])

if __name__ == "__main__":
  application.listen(8083)
  tornado.ioloop.IOLoop.instance().start()
