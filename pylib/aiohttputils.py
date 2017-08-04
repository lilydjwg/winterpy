import os
from http.cookiejar import MozillaCookieJar
from urllib.parse import urljoin

import aiohttp

class ClientBase:
  _session = None
  userAgent = None
  lasturl = None
  auto_referer = False
  baseurl = None
  __our_session = False

  @property
  def session(self):
    if not self._session:
      s = aiohttp.ClientSession()
      self.__our_session = True
      self._session = s
    return self._session

  def __init__(self, *, baseurl=None, cookiefile=None, session=None):
    if baseurl is not None:
      self.baseurl = baseurl
    self._session = session

    s = self.session
    if cookiefile:
      s.cookies = MozillaCookieJar(cookiefile)
      if os.path.exists(cookiefile):
        s.cookies.load()

    self._has_cookiefile = bool(cookiefile)

  def __del__(self):
    if self._has_cookiefile:
      self.session.cookies.save()
    if self.__our_session:
      self.session.close()

  async def request(self, url, method=None, *args, **kwargs):
    if self.baseurl:
      url = urljoin(self.baseurl, url)

    if self.auto_referer and self.lasturl:
      h = kwargs.get('headers', None)
      if not h:
        h = kwargs['headers'] = {}
      h.setdefault('Referer', self.lasturl)

    if self.userAgent:
      h = kwargs.get('headers', None)
      if not h:
        h = kwargs['headers'] = {}
      h.setdefault('User-Agent', self.userAgent)

    if method is None:
      if 'data' in kwargs:
        method = 'post'
      else:
        method = 'get'

    response = await self.session.request(method, url, *args, **kwargs)
    # url may have been changed due to redirection
    self.lasturl = str(response.url)
    return response

async def test():
  client = ClientBase(baseurl='https://www.baidu.com/', cookiefile='test')
  res = await client.request('/')
  res = await client.request('/404')
  print(res, client.lasturl)

if __name__ == '__main__':
  import asyncio
  loop = asyncio.get_event_loop()
  loop.run_until_complete(test())
