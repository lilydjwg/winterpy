'''
HTTP 代理服务器，允许在代理请求的过程中对数据进行读取或者修改

2010年9月18日
'''

import sys
from url import URL
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.client import HTTPConnection
import socketserver

# 其中有些域还未填；放在这里只是为了使代码整洁
directError = r'''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>Error 501</title>
</head><body>
<h1>Error 501: Server does not support this operation</h1>
<p>This server should be used as a HTTP proxy.</p>
<hr>
<address>{server_version} at {domain} Port {port}</address>
</body></html>'''

class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
  pass

class HTTPProxy(BaseHTTPRequestHandler):
  server_version = 'httpproxy/2'
  # 是否处理 HTTP 关于连接的头信息。不处理可能导致连接不关闭
  handleHeaders = True
  def do_remote(self, path, body=None, headers={}):
    '''和远程主机通讯，同时处理501错误（不是代理请求）'''
    if self.handleHeaders:
      del self.headers['Proxy-Connection']
      del self.headers['Keep-Alive']
      del self.headers['Proxy-Authorization']
      self.headers['Connection'] = 'close'

    if not path.scheme:
      self.send_response(501)
      self.send_header('Server', self.server_version)
      self.send_header('Content-Type', 'text/html; charset=utf-8')
      if self.command in ('GET', 'POST'):
        content = directError.format(server_version=self.server_version,
          domain=self.server.server_address[0],
          port=self.server.server_address[1]).encode('utf-8')
      else:
        content = 'Unknown Error'
      self.send_header('Content-Length', str(len(content)))
      self.end_headers()
      self.wfile.write(content)
      self.remoteResponse = None
      return

    client = HTTPConnection(path.netloc)
    headers = dict(headers)
    # 有些网站，比如 WebQQ，在 cookie 中插入了非 ASCII 字符
    # XXX：如果 UTF-8 不适合怎么办？
    for i in headers:
      headers[i] = headers[i].encode('utf-8')
    client.request(self.command, path.getpath(), body, headers)
    self.remoteResponse = client.getresponse()
    self.getdata = self.remoteResponse.read()

  def do_headers(self):
    '''向浏览器发送状态码和响应头
    
    这时远程请求已经完成，可以调用数据处理函数了'''
    self.handle_data()
    self.send_response(self.remoteResponse.status)
    for header in self.remoteResponse.getheaders():
      self.send_header(*header)
    self.end_headers()

  def do_HEAD(self):
    self.do_begin()
    self.url = URL(self.path)
    self.do_remote(self.url, headers=self.headers)
    if not self.remoteResponse:
      return
    self.do_headers()
    self.connection.close()

  def do_GET(self):
    self.do_begin()
    self.url = URL(self.path)
    self.do_remote(self.url, headers=self.headers)
    if not self.remoteResponse:
      return
    self.do_headers()
    self.wfile.write(self.getdata)
    self.connection.close()

  def do_POST(self):
    self.url = URL(self.path)
    self.postdata = self.rfile.read(int(self.headers['content-length']))
    self.do_begin()
    if len(self.postdata) != int(self.headers['content-length']):
        # bad request
        self.send_error(400, 'Post data has wrong length!')
        self.connection.close()
        return
    self.do_remote(self.url, self.postdata, headers=self.headers)
    if not self.remoteResponse:
      return
    self.do_headers()
    self.wfile.write(self.getdata)
    self.connection.close()

  def do_begin(self):
    '''
    开始处理请求了，path/url, command, headers, postdata 可用
    
    可用 headers 的 replace_header() 方法来更改数据，直接赋值无效
    url 是 path 的 URL类版本
    headers 是浏览器发送的头信息
    postdata 是 POST 方法所送出的数据

    handleHeaders 属性在此修改有效。不建议修改该属性。
    '''
    pass

  def handle_data(self):
    '''此时远程处理已完成
    
    可用的数据有：getdata postdata remoteResponse path headers
    可以更改的对象
    getdata 远端返回的数据
    headers 是浏览器发送的头信息
    postdata 是 POST 方法所送出的数据
    remoteResponse.msg 是远端的头信息，
    remoteResponse.status 为状态码'''
    pass

if __name__ == '__main__':
  # httpd = HTTPServer(('', 9999), Proxy)
  # 多线程
  httpd = ThreadingHTTPServer(('', 9999), HTTPProxy)
  print('Server started on 0.0.0.0, port 9999.....')

  # httpd.handle_request()

  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print("\nKeyboard interrupt received, exiting.")
    httpd.server_close()
    sys.exit()
