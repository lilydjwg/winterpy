#!/usr/bin/env python3
# fileencoding=utf-8

'''
一些和HTTP/HTML相关的函数/类

2010年10月22日
'''

import sys, os
from urllib.parse import urlsplit
from urllib.parse import unquote as URIunescape
from http import cookies
# 这个放在这里备用
from urllib.parse import quote as URIescape

class URL(dict):
  '''
  URL，类似于 urllib.parse 中者，但是使用 dict 重构，允许修改数据
  '''

  def __init__(self, url):
    o = urlsplit(url)
    dict.__init__(self, {
        'scheme':   o.scheme,
        'netloc':   o.netloc,
        'path':     o.path,
        'query':    o.query,
        'fragment': o.fragment,
        'username': o.username,
        'password': o.password,
        'hostname': o.hostname,
        'port':     o.port,
        })

  def geturl(self):
    url = '//' + self['netloc']
    if self['port']:
      url = url + ':' + self['port']
    if self['scheme']:
      url = self['scheme'] + ':' + url
    url += self.getpath()
    return url

  def getpath(self):
    '''返回 URL 中域名之后的部分'''
    url = self['path']
    if self['query']:
      url = url + '?' + self['query']
    if self['fragment']:
      url = url + '#' + self['fragment']
    return url

  def __setattr__(self, name, value):
    dict.__setitem__(self, name, value)

  def __getattr__(self, name):
    return dict.__getitem__(self, name)

  def __delattr__(self, name):
    dict.__delitem__(self, name)

class Cookie(cookies.SimpleCookie):
  def __init__(self, file=None):
    self.data = {}
    if file:
      self.loadFromFile(file)
      self.file = file

  def loadFromFile(self, file):
    '''从文件载入。文件中每行一条 cookie 信息'''
    try:
      l = open(file).readlines()
      l = [i[i.find(' ')+1:].strip() for i in l]
      self.add(l)
    except IOError as e:
      if e.errno == 2:
        #文件尚未建立
        pass
      else:
        raise

  def add(self, data):
    '''加入或更新一条 cookie 信息，其格式为 name=value'''
    if isinstance(data, (list, tuple)):
      for i in data:
        self.add(i)
    else:
      name, value = data.split(';')[0].split('=')
      self[name] = value

  def addFromResponse(self, response):
    '''从 Response 对象加入/更新 Cookie'''
    self.add([i[1] for i in response.info().items() if i[0] == 'Set-Cookie'])

  def sendFormat(self):
    '''发送格式：key=value; key=value'''
    ret = ''
    for i in self.keys():
      ret += i+'='+self[i].value+'; '
    return ret[:-2]
  
  def __del__(self):
    '''自动保存'''
    if self.file:
      open(self.file, 'w').write(str(self))
      os.chmod(self.file, 0o600)

  def __bool__(self):
    return bool(self.data)

class PostData:
  def __init__(self, data=None):
    '''data 可为 dict, str, bytes 或 None，最终得到的为 bytes'''
    self.data = b''
    if isinstance(data, dict):
      for k, v in data.items():
        self.add(k, v)
    elif isinstance(data, bytes):
      self.data = data
    elif isinstance(data, str):
      self.data = data.encode('utf-8')
    elif data is None:
      pass
    else:
      raise TypeError('data 类型（%s）不正确' % data.__class__.__name__)

  def add(self, key, value):
    '''添加键值对，key 和 value 要求为 str'''
    key = key.encode('utf-8')
    value = value.encode('utf-8')
    self.data += b'&'+key+b'='+value if self.data else key+b'='+value

  def __bool__(self):
    return bool(self.data)

def parseQuery(query):
  '''解析 URL 中的 query 部分，返回 dict'''
  items = query.split('&')
  ret = {}
  for x in items:
    x = x.split('=')
    ret[x[0]] = URIunescape(x[1])
  return ret

def urlopen(url, headers={}, proxy=None, timeout=5):
  '''打开 URL，返回 HTTPResponse 对象和新建的连接
  只支持 HTTP 和 HTTPS'''

  if not isinstance(url, URL):
    raise TypeError('URL object expected')

  import http.client
  host = proxy and URL(proxy).netloc or url.netloc
  if url.scheme == 'http':
    conn = http.client.HTTPConnection(host, timeout=timeout)
  elif url.scheme == 'https':
    conn = http.client.HTTPSConnection(host, timeout=timeout)
  else:
    raise http.client.UnknownProtocol('不支持的协议类型：%s' % url.scheme)

  if proxy:
    conn.putrequest('GET', url.geturl().split('#')[0])
  else:
    conn.putrequest('GET', url.getpath().split('#')[0])
  for k, v in headers.items():
    conn.putheader(k, v)
  conn.endheaders()

  return conn.getresponse(), conn

def entityunescape(string):
  '''HTML 实体反转义'''
  from html.entities import entitydefs
  import re

  def sharp2uni(m):
    '''&#...; ==> unicode'''
    s = m.group(0)[2:-1]
    if s.startswith('x'):
      return chr(int('0'+s, 16))
    else:
      return chr(int(s))

  string = re.sub(r'&#[^;]+;', sharp2uni, string)
  string = re.sub(r'&[^;]+;', lambda m: entitydefs[m.group(0)[1:-1]], string)

  return string
def encode_multipart_formdata(fields, files, boundary=None):
  """
  fields is a sequence of (name, value) elements for regular form fields.
  files is a sequence of (name, filename, value) elements for data to be uploaded as files
  Return (content_type, body) ready for httplib.HTTP instance

  from: http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
  """
  BOUNDARY = boundary or '----------ThIs_Is_tHe_bouNdaRY_$'
  CRLF = '\r\n'
  L = []
  for (key, value) in fields:
    L.append('--' + BOUNDARY)
    L.append('Content-Disposition: form-data; name="%s"' % key)
    L.append('')
    L.append(value)
  for (key, filename, value) in files:
    L.append('--' + BOUNDARY)
    L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
    L.append('Content-Type: %s' % get_content_type(filename))
    L.append('')
    L.append(value)
  L.append('--' + BOUNDARY + '--')
  L.append('')
  body = CRLF.join(L)
  content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
  return content_type, body

def get_content_type(filename):
  '''
  from: http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
  '''
  import mimetypes
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
