import os
from http.cookiejar import MozillaCookieJar
from urllib.parse import urljoin
from typing import Optional
import asyncio

import aiohttp
from aiohttp.client import ClientResponse

class ClientBase:
  session = None
  userAgent = None
  lasturl = None
  auto_referer = False
  baseurl: Optional[str] = None
  cookiefile: Optional[os.PathLike] = None
  __our_session: bool = False

  def __init__(self, *, baseurl=None, cookiefile=None, session=None):
    if baseurl is not None:
      self.baseurl = baseurl
    self.session = session
    self.cookiefile = cookiefile

  async def async_init(self) -> None:
    if not self.session:
      s = aiohttp.ClientSession()
      self.__our_session = True
      self.session = s

      if self.cookiefile:
        s.cookies = MozillaCookieJar(self.cookiefile)
        if os.path.exists(self.cookiefile):
          s.cookies.load() # type: ignore

  def __del__(self):
    if self.cookiefile:
      self.session.cookies.save()
    if self.__our_session:
      loop = asyncio.get_event_loop()
      closer = self.session.close()
      if loop.is_running():
        asyncio.ensure_future(closer)
      else:
        asyncio.run(closer)

  async def request(
    self, url: str, method: Optional[str] = None, **kwargs,
  ) -> ClientResponse:
    if not self.session:
      await self.async_init()

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

    response = await self.session.request(method, url, **kwargs) # type: ignore
    # url may have been changed due to redirection
    self.lasturl = str(response.url)
    return response

async def test():
  client = ClientBase(baseurl='https://www.baidu.com/', cookiefile='test')
  res = await client.request('/')
  res = await client.request('/404')
  print(res, client.lasturl)

if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(test())
