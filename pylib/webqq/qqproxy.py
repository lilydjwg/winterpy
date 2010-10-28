#!/usr/bin/env python3
# vim:fileencoding=utf-8

from httpproxy2 import HTTPProxy
import socketserver
from http.server import HTTPServer
from url import URL

class QQProxy(HTTPProxy):
  '''WebQQ 代理处理'''
  def handle_msg(self, msg, direction):
    '''实际处理消息的方法，应当被子类重写'''
    pass

  def do_begin(self):
    u = URL(self.path)
    if u.path != '/conn_s' or not u.netloc.endswith('qq.com'):
      # 不是QQ通讯消息
      return
    for i in self.postdata.decode().split('\x1d'):
      self.handle_msg(i, 'sent')
    assert self.command == 'POST'

  def handle_data(self):
    '''处理 HTTP 消息，调用 QQ 消息处理方法 handle_msg'''
    u = URL(self.path)
    if u.path != '/conn_s' or not u.netloc.endswith('qq.com'):
      # 不是QQ通讯消息
      return
    for i in self.getdata.decode().split('\x1d'):
      self.handle_msg(i, 'recved')
    assert self.command == 'POST'

  def log_request(self, code='-', size='-'):
    pass

class _ThreadingQQProxyServer(socketserver.ThreadingMixIn, HTTPServer):
  '''多线程服务'''
  pass

def ThreadingQQProxyServer(server_address, msgHandler):
  class NewQQProxy(QQProxy):
    def handle_msg(self, msg, direction):
      msgHandler(msg, direction)
  return _ThreadingQQProxyServer(server_address, NewQQProxy)

