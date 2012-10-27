# vim:fileencoding=utf-8

import re
import socket
from urllib.parse import urlsplit
from functools import partial
from collections import namedtuple
import logging

import tornado.ioloop
import tornado.iostream

# try to import C parser then fallback in pure python parser.
try:
  from http_parser.parser import HttpParser
except ImportError:
  from http_parser.pyparser import HttpParser

class SingletonFactory:
  def __init__(self, name):
    self.name = name
  def __repr__(self):
    return '<%s>' % self.name

MediaType = namedtuple('MediaType', 'type size')

ConnectionClosed = SingletonFactory('ConnectionClosed')
TooManyRedirection = SingletonFactory('TooManyRedirection')
Timeout = SingletonFactory('Timeout')

logger = logging.getLogger(__name__)

class TitleFinder:
  found = None
  title_begin = re.compile(b'<title[^>]*>', re.IGNORECASE)
  title_end = re.compile(b'</title>', re.IGNORECASE)
  buf = b''
  pos = 0

  def __call__(self, data):
    self.buf += data
    self.pos += len(data)
    if len(self.buf) < 100:
      return
    if self.found is None:
      m = self.title_begin.search(self.buf)
      if m:
        self.found = m.end()
    if self.found is not None:
      m = self.title_end.search(self.buf, self.found)
      if m:
        raw_title = self.buf[self.found:m.start()].strip()
        logger.debug('title found at %d', self.pos - len(self.buf) + m.start())
        return raw_title
    if self.found is None:
      self.buf = self.buf[-100:]

class TitleFetcher:
  charset = 'UTF-8' # default charset
  status_code = 0
  followed_times = 0 # 301, 302
  addr = None
  stream = None
  max_follows = 10
  timeout = 15
  _return_once = False

  def __init__(self, url, callback,
               timeout=None, max_follows=None, io_loop=None):
    '''
    url: the (full) url to fetch
    callback: called with title or MediaType or an instance of SingletonFactory
    timeout: total time including redirection before giving up
    max_follows: max redirections
    '''
    self._callback = callback
    if max_follows is not None:
      self.max_follows = max_follows

    if timeout is not None:
      self.timeout = timeout
    self.io_loop = io_loop or tornado.ioloop.IOLoop.instance()

    self.start_time = self.io_loop.time()
    self._timeout = self.io_loop.add_timeout(
      self.timeout + self.start_time,
      self.on_timeout,
    )
    self.fullurl = url
    self.new_url(url)

  def on_timeout(self):
    self.run_callback(Timeout)

  def parse_url(self, url):
    '''parse `url`, set self.host and return address and stream class'''
    self.url = u = urlsplit(url)

    self.host = u.netloc
    try:
      host, port = u.netloc.rsplit(':', 1)
    except ValueError:
      host = u.netloc
      port = 0
    else:
      port = int(port)

    if u.scheme == 'http':
      addr = host, port or 80
      stream = tornado.iostream.IOStream
    elif u.scheme == 'https':
      addr = host, port or 443
      stream = tornado.iostream.SSLIOStream
    else:
      raise ValueError('bad url: %r' % url)

    return addr, stream

  def new_connection(self, addr, StreamClass):
    '''set self.addr, self.stream and connect to host'''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.addr = addr
    self.stream = StreamClass(s)
    logger.debug('%s: connecting to %s...', self.fullurl, addr)
    self.stream.connect(addr, self.send_request)

  def new_url(self, url):
    addr, StreamClass = self.parse_url(url)
    if addr != self.addr:
      if self.stream:
        self._return_once = True
        self.stream.close()
      self.new_connection(addr, StreamClass)
    else:
      logger.debug('%s: reuse existing connection to %s', self.fullurl, self.addr)
      self.send_request(nocallback=True)

  def run_callback(self, arg):
    self.io_loop.remove_timeout(self._timeout)
    self.stream.close()
    self._callback(arg, self)

  def send_request(self, nocallback=False):
    req = ('GET %s HTTP/1.1',
           'Host: %s',
           'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0',
           'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.7',
           'Accept-Language: zh-cn,zh;q=0.7,en;q=0.3',
           'Accept-Charset: utf-8,gb18030;q=0.7,*;q=0.7',
           'Accept-Encoding: gzip, deflate',
           'Connection: keep-alive',
          )
    path = self.url.path or '/'
    if self.url.query:
      path += '?' + self.url.query
    req = '\r\n'.join(req) % (
      path, self.host,
    ) + '\r\n\r\n'
    self.stream.write(req.encode())
    self.headers_done = False
    self.parser = HttpParser(decompress=True)
    self.finder = TitleFinder()
    if not nocallback:
      self.stream.read_until_close(
        # self.addr will have been changed when close callback is run
        partial(self.on_data, close=True, addr=self.addr),
        streaming_callback=self.on_data,
      )

  def on_data(self, data, close=False, addr=None):
    if close:
      logger.debug('%s: connection to %s closed.', self.fullurl, addr)

    if self._return_once:
      self._return_once = False
      # The connection is closing, and we haven't run the callback because of
      # redirection.
      return

    recved = len(data)
    logger.debug('%s: received data: %d bytes', self.fullurl, recved)

    p = self.parser
    nparsed = p.execute(data, recved)

    if not self.headers_done and p.is_headers_complete():
      self.headers_done = True
      self.headers = p.get_headers()

      self.status_code = p.get_status_code()
      if self.status_code in (301, 302):
        logger.debug('%s: redirect to %s', self.fullurl, self.headers['Location'])
        self.followed_times += 1
        if self.followed_times > self.max_follows:
          self.run_callback(TooManyRedirection)
        else:
          self.new_url(self.headers['Location'])
        return

      ctype = self.headers.get('Content-Type', 'text/html')
      if ctype.find('html') == -1:
        l = self.headers.get('Content-Length', None)
        self.run_callback(MediaType(ctype, l))
        return
      pos = ctype.find('charset=')
      if pos > 0:
        self.charset = ctype[pos+8:]

    if p.is_partial_body():
      chunk = p.recv_body()
      t = self.finder(chunk)
      if t:
        try:
          self.run_callback(t.decode(self.charset))
        except (UnicodeDecodeError, LookupError):
          self.run_callback(t)
        return

    if p.is_message_complete():
      # title not found
      self.run_callback(None)
    elif close:
      self.run_callback(ConnectionClosed)

def main(urls):
  class BatchFetcher:
    n = 0
    def __call__(self, title, fetcher):
      logger.info('done: [%d] %s <- %s' % (fetcher.status_code, title, fetcher.fullurl))
      self.n -= 1
      if not self.n:
        tornado.ioloop.IOLoop.instance().stop()

    def add(self, url):
      TitleFetcher(url, self)
      self.n += 1

  from myutils import enable_pretty_logging
  enable_pretty_logging()
  f = BatchFetcher()
  for u in urls:
    f.add(u)
  tornado.ioloop.IOLoop.instance().start()

def test():
  urls = (
    'http://lilydjwg.is-programmer.com/',
    'http://www.baidu.com',
    'https://zh.wikipedia.org', # redirection
    'http://blog.binux.me/yaaw/demo/###',
    'http://redis.io/',
    'http://kernel.org',
    'http://lilydjwg.is-programmer.com/2012/10/27/streaming-gzip-decompression-in-python.36130.html', # maybe timeout
    'http://www.vim.org',
    'http://img.vim-cn.com/22/cd42b4c776c588b6e69051a22e42dabf28f436', # image with length
    'https://github.com/m13253/titlebot/blob/master/titlebot.py_', # 404
    'http://lilydjwg.is-programmer.com/admin', # redirection
    'http://p.vim-cn.com/ddV', # plain text without length
    'http://twitter.com', # timeout
    'http://www.wordpress.com', # reset
    'https://www.wordpress.com', # timeout
    'http://jquery-api-zh-cn.googlecode.com/svn/trunk/xml/jqueryapi.xml', # xml
  )
  main(urls)

if __name__ == "__main__":
  import sys
  if len(sys.argv) == 1:
    sys.exit('no urls given.')
  elif sys.argv[1] == 'test':
    test()
  else:
    main(sys.argv[1:])
