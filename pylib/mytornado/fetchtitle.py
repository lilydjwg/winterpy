# vim:fileencoding=utf-8

import re
import socket
from urllib.parse import urlsplit, urljoin
from functools import partial
from collections import namedtuple
import struct
import json
import logging
import encodings.idna
try:
  # Python 3.3
  from html.entities import html5 as _entities
  def _extract_entity_name(m):
    return m.group()[1:]
except ImportError:
  from html.entities import entitydefs as _entities
  def _extract_entity_name(m):
    return m.group()[1:-1]

import tornado.ioloop
import tornado.iostream

# try to import C parser then fallback in pure python parser.
try:
  from http_parser.parser import HttpParser
except ImportError:
  from http_parser.pyparser import HttpParser

UserAgent = 'FetchTitle/1.1 (lilydjwg@gmail.com)'
class SingletonFactory:
  def __init__(self, name):
    self.name = name
  def __repr__(self):
    return '<%s>' % self.name

MediaType = namedtuple('MediaType', 'type size dimension')
defaultMediaType = MediaType('application/octet-stream', None, None)

ConnectionClosed = SingletonFactory('ConnectionClosed')
TooManyRedirection = SingletonFactory('TooManyRedirection')
Timeout = SingletonFactory('Timeout')

logger = logging.getLogger(__name__)

def _sharp2uni(code):
  '''&#...; ==> unicode'''
  s = code[1:].rstrip(';')
  if s.startswith('x'):
    return chr(int('0'+s, 16))
  else:
    return chr(int(s))

def _mapEntity(m):
  name = _extract_entity_name(m)
  if name.startswith('#'):
    return _sharp2uni(name)
  try:
    return _entities[name]
  except KeyError:
    return '&' + name

def replaceEntities(s):
  return re.sub(r'&[^;]+;', _mapEntity, s)

class ContentFinder:
  buf = b''
  def __init__(self, mediatype):
    self._mt = mediatype

  @classmethod
  def match_type(cls, mediatype):
    ctype = mediatype.type.split(';', 1)[0]
    if hasattr(cls, '_mime') and cls._mime == ctype:
      return cls(mediatype)
    if hasattr(cls, '_match_type') and cls._match_type(ctype):
      return cls(mediatype)
    return False

class TitleFinder(ContentFinder):
  found = None
  title_begin = re.compile(b'<title[^>]*>', re.IGNORECASE)
  title_end = re.compile(b'</title>', re.IGNORECASE)
  pos = 0

  default_charset = 'UTF-8'
  meta_charset = re.compile(br'<meta\s+http-equiv="?content-type"?\s+content="?[^;]+;\s*charset=([^">]+)"?\s*/?>|<meta\s+charset="?([^">/"]+)"?\s*/?>', re.IGNORECASE)
  charset = None

  @staticmethod
  def _match_type(ctype):
    return ctype.find('html') != -1

  def __init__(self, mediatype):
    ctype = mediatype.type
    pos = ctype.find('charset=')
    if pos > 0:
      self.charset = ctype[pos+8:]
      if self.charset.lower() == 'gb2312':
        # Windows misleadingly uses gb2312 when it's gbk or gb18030
        self.charset = 'gb18030'

  def __call__(self, data):
    if data is not None:
      self.buf += data
      self.pos += len(data)
      if len(self.buf) < 100:
        return

    buf = self.buf

    if self.charset is None:
      m = self.meta_charset.search(buf)
      if m:
        self.charset = (m.group(1) or m.group(2)).decode('latin1')

    if self.found is None:
      m = self.title_begin.search(buf)
      if m:
        self.found = m.end()
    if self.found is not None:
      m = self.title_end.search(buf, self.found)
      if m:
        raw_title = buf[self.found:m.start()].strip()
        logger.debug('title found at %d', self.pos - len(buf) + m.start())
        return self.decode_title(raw_title)
    if self.found is None:
      self.buf = buf[-100:]

  def decode_title(self, raw_title):
    try:
      title = replaceEntities(raw_title.decode(self.get_charset()))
      return title
    except (UnicodeDecodeError, LookupError):
      return raw_title

  def get_charset(self):
    return self.charset or self.default_charset

class PNGFinder(ContentFinder):
  _mime = 'image/png'
  def __call__(self, data):
    if data is None:
      return self._mt

    self.buf += data
    if len(self.buf) < 24:
      # can't decide yet
      return
    if self.buf[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR':
      logging.warn('Bad PNG signature and header: %r', self.buf[:16])
      return self._mt._replace(dimension='Bad PNG')
    else:
      s = struct.unpack('!II', self.buf[16:24])
      return self._mt._replace(dimension=s)

class JPEGFinder(ContentFinder):
  _mime = 'image/jpeg'
  isfirst = True
  def __call__(self, data):
    if data is None:
      return self._mt

    # http://www.64lines.com/jpeg-width-height
    if data:
      self.buf += data

    if self.isfirst is True:
      # finding header
      if len(self.buf) < 5:
        return
      if self.buf[:3] != b'\xff\xd8\xff':
        logging.warn('Bad JPEG signature: %r', self.buf[:3])
        return self._mt._replace(dimension='Bad JPEG')
      else:
        self.blocklen = self.buf[4] * 256 + self.buf[5] + 2
        self.buf = self.buf[2:]
        self.isfirst = False

    if self.isfirst is False:
      # receiving a block. 4 is for next block size
      if len(self.buf) < self.blocklen + 4:
        return
      buf = self.buf
      if buf[0] != 0xff:
        logging.warn('Bad JPEG: %r', self.buf[:self.blocklen])
        return self._mt._replace(dimension='Bad JPEG')
      if buf[1] == 0xc0 or buf[1] == 0xc2:
        s = buf[7] * 256 + buf[8], buf[5] * 256 + buf[6]
        return self._mt._replace(dimension=s)
      else:
        # not Start Of Frame, retry with next block
        self.buf = buf = buf[self.blocklen:]
        self.blocklen = buf[2] * 256 + buf[3] + 2
        return self(b'')

class GIFFinder(ContentFinder):
  _mime = 'image/gif'
  def __call__(self, data):
    if data is None:
      return self._mt

    self.buf += data
    if len(self.buf) < 10:
      # can't decide yet
      return
    if self.buf[:3] != b'GIF':
      logging.warn('Bad GIF signature: %r', self.buf[:3])
      return self._mt._replace(dimension='Bad GIF')
    else:
      s = struct.unpack('<HH', self.buf[6:10])
      return self._mt._replace(dimension=s)

class TitleFetcher:
  status_code = 0
  followed_times = 0 # 301, 302
  finder = None
  addr = None
  stream = None
  max_follows = 10
  timeout = 15
  _finished = False
  _cookie = None
  _connected = False
  _redirected_stream = None
  _content_finders = (TitleFinder, PNGFinder, JPEGFinder, GIFFinder)
  _url_finders = ()

  def __init__(self, url, callback,
               timeout=None, max_follows=None, io_loop=None,
               content_finders=None, url_finders=None
              ):
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
    if hasattr(tornado.ioloop, 'current'):
        default_io_loop = tornado.ioloop.IOLoop.current
    else:
        default_io_loop = tornado.ioloop.IOLoop.instance
    self.io_loop = io_loop or default_io_loop()

    if content_finders is not None:
      self._content_finders = content_finders
    if url_finders is not None:
      self._url_finders = url_finders

    self.start_time = self.io_loop.time()
    self._timeout = self.io_loop.add_timeout(
      self.timeout + self.start_time,
      self.on_timeout,
    )
    self.origurl = url
    self.url_visited = []
    self.new_url(url)

  def on_timeout(self):
    self.run_callback(Timeout)

  def parse_url(self, url):
    '''parse `url`, set self.host and return address and stream class'''
    self.url = u = urlsplit(url)
    self.host = u.netloc

    if u.scheme == 'http':
      addr = u.hostname, u.port or 80
      stream = tornado.iostream.IOStream
    elif u.scheme == 'https':
      addr = u.hostname, u.port or 443
      stream = tornado.iostream.SSLIOStream
    else:
      raise ValueError('bad url: %r' % url)

    return addr, stream

  def new_connection(self, addr, StreamClass):
    '''set self.addr, self.stream and connect to host'''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.addr = addr
    self.stream = StreamClass(s)
    logger.debug('%s: connecting to %s...', self.origurl, addr)
    self.stream.set_close_callback(self.before_connected)
    self.stream.connect(addr, self.send_request)

  def new_url(self, url):
    self.url_visited.append(url)
    self.fullurl = url

    for finder in self._url_finders:
      f = finder.match_url(url, self)
      if f:
        self.finder = f
        f()
        return

    addr, StreamClass = self.parse_url(url)
    if addr != self.addr:
      if self.stream:
        self.stream.close()
      self.new_connection(addr, StreamClass)
    else:
      logger.debug('%s: try to reuse existing connection to %s', self.origurl, self.addr)
      try:
        self.send_request(nocallback=True)
      except tornado.iostream.StreamClosedError:
        logger.debug('%s: server at %s doesn\'t like keep-alive, will reconnect.', self.origurl, self.addr)
        # The close callback should have already run
        self.stream.close()
        self.new_connection(addr, StreamClass)

  def run_callback(self, arg):
    self.io_loop.remove_timeout(self._timeout)
    self._finished = True
    if self.stream:
      self.stream.close()
    self._callback(arg, self)

  def send_request(self, nocallback=False):
    self._connected = True
    req = ('GET %s HTTP/1.1',
           'Host: %s',
           # t.co will return 200 and use js/meta to redirect using the following :-(
           # 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0',
           'User-Agent: %s' % UserAgent,
           'Accept: text/html,application/xhtml+xml;q=0.9,*/*;q=0.7',
           'Accept-Language: zh-cn,zh;q=0.7,en;q=0.3',
           'Accept-Charset: utf-8,gb18030;q=0.7,*;q=0.7',
           'Accept-Encoding: gzip, deflate',
           'Connection: keep-alive',
          )
    path = self.url.path or '/'
    if self.url.query:
      path += '?' + self.url.query
    req = '\r\n'.join(req) % (
      path, self._prepare_host(self.host),
    )
    if self._cookie:
      req += '\r\n' + self._cookie
    req += '\r\n\r\n'
    self.stream.write(req.encode())
    self.headers_done = False
    self.parser = HttpParser(decompress=True)
    if not nocallback:
      self.stream.read_until_close(
        # self.addr will have been changed when close callback is run
        partial(self.on_data, close=True, addr=self.addr),
        streaming_callback=self.on_data,
      )

  def _prepare_host(self, host):
    host = encodings.idna.nameprep(host)
    return b'.'.join(encodings.idna.ToASCII(x) for x in host.split('.')).decode('ascii')

  def on_data(self, data, close=False, addr=None):
    if close:
      logger.debug('%s: connection to %s closed.', self.origurl, addr)

    if (close and self._redirected_stream is self.stream) or self._finished:
      # The connection is closing, and we are being redirected or we're done.
      self._redirected_stream = None
      return

    recved = len(data)
    logger.debug('%s: received data: %d bytes', self.origurl, recved)

    p = self.parser
    nparsed = p.execute(data, recved)
    if close:
      # feed EOF
      p.execute(b'', 0)

    if not self.headers_done and p.is_headers_complete():
      if not self.on_headers_done():
        return

    if p.is_partial_body():
      chunk = p.recv_body()
      if self.finder is None:
        # redirected but has body received
        return
      t = self.feed_finder(chunk)
      if t is not None:
        self.run_callback(t)
        return

    if p.is_message_complete():
      if self.finder is None:
        # redirected but has body received
        return
      t = self.feed_finder(None)
      # if title not found, t is None
      self.run_callback(t)
    elif close:
      self.run_callback(self.stream.error or ConnectionClosed)

  def before_connected(self):
    '''check if something wrong before connected'''
    if not self._connected and not self._finished:
      self.run_callback(self.stream.error)

  def process_cookie(self):
    setcookie = self.headers.get('Set-Cookie', None)
    if not setcookie:
      return

    cookies = [c.rsplit(None, 1)[-1] for c in setcookie.split('; expires')[:-1]]
    self._cookie = 'Cookie: ' + '; '.join(cookies)

  def on_headers_done(self):
    '''returns True if should proceed, None if should stop for current chunk'''
    self.headers_done = True
    self.headers = self.parser.get_headers()

    self.status_code = self.parser.get_status_code()
    if self.status_code in (301, 302):
      self.process_cookie() # or we may be redirecting to a loop
      logger.debug('%s: redirect to %s', self.origurl, self.headers['Location'])
      self.followed_times += 1
      if self.followed_times > self.max_follows:
        self.run_callback(TooManyRedirection)
      else:
        newurl = urljoin(self.fullurl, self.headers['Location'])
        self._redirected_stream = self.stream
        self.new_url(newurl)
      return

    try:
      l = int(self.headers.get('Content-Length', None))
    except (ValueError, TypeError):
      l = None

    ctype = self.headers.get('Content-Type', 'text/html')
    mt = defaultMediaType._replace(type=ctype, size=l)
    for finder in self._content_finders:
      f = finder.match_type(mt)
      if f:
        self.finder = f
        break
    else:
      self.run_callback(mt)
      return

    return True

  def feed_finder(self, chunk):
    '''feed data to TitleFinder, return the title if found'''
    t = self.finder(chunk)
    if t is not None:
      return t

class URLFinder:
  def __init__(self, url, fetcher, match=None):
    self.fullurl = url
    self.match = match
    self.fetcher = fetcher

  @classmethod
  def match_url(cls, url, fetcher):
    if hasattr(cls, '_url_pat'):
      m = cls._url_pat.match(url)
      if m is not None:
        return cls(url, fetcher, m)
    if hasattr(cls, '_match_url') and cls._match_url(url, fetcher):
      return cls(url, fetcher)

  def done(self, info):
    self.fetcher.run_callback(info)

class GithubFinder(URLFinder):
  _url_pat = re.compile(r'https://github\.com/(?P<repo_path>[^/]+/[^/]+)/?$')
  _api_pat = 'https://api.github.com/repos/{repo_path}'
  httpclient = None

  def __call__(self):
    if self.httpclient is None:
      from tornado.httpclient import AsyncHTTPClient
      httpclient = AsyncHTTPClient()
    else:
      httpclient = self.httpclient

    m = self.match
    httpclient.fetch(self._api_pat.format(**m.groupdict()), self.parse_info,
                     headers={
                       'User-Agent': UserAgent,
                     })

  def parse_info(self, res):
    repoinfo = json.loads(res.body.decode('utf-8'))
    self.done(repoinfo)

class GithubUserFinder(GithubFinder):
  _url_pat = re.compile(r'https://github\.com/(?P<user>[^/]+)$')
  _api_pat = 'https://api.github.com/users/{user}'

def main(urls):
  class BatchFetcher:
    n = 0
    def __call__(self, title, fetcher):
      if isinstance(title, bytes):
        try:
          title = title.decode('gb18030')
        except UnicodeDecodeError:
          pass
      url = ' <- '.join(reversed(fetcher.url_visited))
      logger.info('done: [%d] %s <- %s' % (fetcher.status_code, title, url))
      self.n -= 1
      if not self.n:
        tornado.ioloop.IOLoop.instance().stop()

    def add(self, url):
      TitleFetcher(url, self, url_finders=(GithubFinder,))
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
    'http://lilydjwg.is-programmer.com/user_files/lilydjwg/config/avatar.png', # PNG
    'http://img01.taobaocdn.com/bao/uploaded/i1/110928240/T2okG7XaRbXXXXXXXX_!!110928240.jpg', # JPEG with Start Of Frame as the second block
    'http://file3.u148.net/2013/1/images/1357536246993.jpg', # JPEG that failed previous code
    'http://gouwu.hao123.com/', # HTML5 GBK encoding
    'https://github.com/lilydjwg/winterpy', # github url finder
    'http://github.com/lilydjwg/winterpy', # github url finder with redirect
    'http://导航.中国/', # Punycode. This should not be redirected
    'http://t.cn/zTOgr1n', # multiple redirections
  )
  main(urls)

if __name__ == "__main__":
  import sys
  try:
    if len(sys.argv) == 1:
      sys.exit('no urls given.')
    elif sys.argv[1] == 'test':
      test()
    else:
      main(sys.argv[1:])
  except KeyboardInterrupt:
    print('Interrupted.')
