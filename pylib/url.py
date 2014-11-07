'''
一些和HTTP/HTML相关的函数/类
'''

import sys, os
from urllib.parse import urlsplit, urlencode
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

def encode_url_params(data):
  '''
  为 URL 编码数据

  data 可为 dict, str, bytes 或 None，最终得到的为 bytes
  '''
  if isinstance(data, dict):
    ret = urlencode(data)
  elif isinstance(data, bytes):
    ret = data
  elif isinstance(data, str):
    ret = data.encode('utf-8')
  else:
    raise TypeError('data 类型（%s）不支持' % data.__class__.__name__)
  return ret

def encode_multipart_formdata(fields, files, boundary=None):
  """
  fields is a sequence of (name, value) elements for regular form fields.
  files is a sequence of (name, filename, value) elements for data to be
    uploaded as files
  All items can be either str or bytes

  Return (content_type, body) ready for httplib.HTTP instance, body will be
  bytes

  from: http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
  """
  BOUNDARY = boundary or '----------ThIs_Is_tHe_bouNdaRY_$'
  CRLF = b'\r\n'
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
  L = map(lambda x: x.encode('utf-8') if isinstance(x, str) else x, L)
  body = CRLF.join(L)
  content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
  return content_type, body

def get_content_type(filename):
  '''
  from: http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
  '''
  import mimetypes
  return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
