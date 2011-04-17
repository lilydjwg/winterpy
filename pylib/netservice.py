#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
提供网络信息获取服务
'''
from url import *

def getTitle(url, headers={}, timeout=5):
  '''
  获取网页标题，url 要指定协议的

  如果字符串解码失败，返回 bytes
  如果不是网页返回 None

  可能出现的异常
    socket.error: [Errno 111] Connection refused
    socket.timeout: timed out
  '''
  # TODO 对 meta 刷新的处理
  import re
  import socket
  from httpsession import Session

  defaultheaders = {}
  defaultheaders['User-Agent'] = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6'
  defaultheaders['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.7'
  defaultheaders['Accept-Language'] = 'zh-cn,zh;q=0.5'
  defaultheaders['Accept-Charset'] = 'utf-8,gb18030;q=0.7,*;q=0.7'
  defaultheaders.update(headers)
  headers = defaultheaders

  s = Session()
  try:
    response = s.request(url, headers=headers)
  except socket.error:
    response = s.request(url, headers=headers, proxy={
      'http':  'http://localhost:8000',
      'https': 'http://localhost:8000',
    })

  contentType = response.getheader('Content-Type', default='text/html')
  type = contentType.split(';', 1)[0]
  if type.find('html') == -1 and type.find('xml') == -1:
    return None

  try:
    charset = contentType.rsplit('=', 1)[1]
  except IndexError:
    charset = None
  # 1024 对于 Twitter 来说太小了
  content = response.read(10240)

  title = b''
  m = re.search(b'<title[^>]*>([^<]*)', content, re.IGNORECASE)
  if m:
    title = m.group(1)

  if charset is None:
    import chardet
    title = title.decode(chardet.detect(title)['encoding'])
  else:
    if charset.lower().find('big5') != -1:
      charset = 'big5'
    title = title.decode(charset)
  title = entityunescape(title.replace('\n', '')).strip()

  return title or None

def translate(q, langpair='|zh', hl='zh'):
  '''使用 Google 翻译文本
  http://code.google.com/intl/zh-CN/apis/ajaxlanguage/documentation/reference.html
  '''
  import json
  import urllib.request

  url = 'http://ajax.googleapis.com/ajax/services/language/translate'
  url += '?format=text&v=1.0&hl=zh&langpair=%s&q=%s' % (
      URIescape(langpair), URIescape(q))
  ans = urllib.request.urlopen(url, timeout=5).read().decode('utf-8')
  ans = json.loads(ans)
  if ans['responseStatus'] != 200:
    raise Exception(ans)

  return ans['responseData']['translatedText']

def ubuntuPaste(poster='', screenshot='', code2='',
    klass='bash', filename=None):
  '''
  paste 到 http://paste.ubuntu.org.cn/
  screenshot 是文件路径

  返回查看此帖子的 URL （字符串）
  '''
  from httpsession import Session
  paste_url = 'http://paste.ubuntu.org.cn/'
  fields = [
    ('paste',  'send'),
    ('poster', poster),
    ('code2',  code2),
    ('class',  klass),
  ]
  if screenshot:
    files = (
      ('screenshot', filename or os.path.split(screenshot)[1], open(screenshot, 'rb').read()),
    )
  else:
    files = ()

  data = encode_multipart_formdata(fields, files)
  s = Session()
  r = s.request(paste_url, data[1], headers={
    'Content-Type': data[0],
    'Expect': '100-continue',
  })
  return r.geturl()

