import os
from http.cookiejar import MozillaCookieJar
from urllib.parse import urljoin
from typing import Optional

import httpx

type Path = str | bytes | os.PathLike

class ClientBase:
  session: Optional[httpx.Client] = None
  userAgent: Optional[str] = None
  lasturl: Optional[str] = None
  auto_referer: bool = False
  baseurl: Optional[str] = None
  cookiefile: Optional[Path] = None

  def __init__(
    self, *,
    baseurl: Optional[str] = None,
    cookiefile: Optional[Path] = None,
    session: Optional[httpx.Client] = None,
  ) -> None:
    if baseurl is not None:
      self.baseurl = baseurl
    self.session = session
    self.cookiefile = cookiefile

  def async_init(self) -> None:
    if not self.session:
      s = httpx.Client(http2=True)
      self.session = s

      if self.cookiefile:
        cookiejar = MozillaCookieJar(self.cookiefile) # type: ignore
        if os.path.exists(self.cookiefile):
          cookiejar.load()
        s.cookies = cookiejar

  def __del__(self):
    if self.cookiefile:
      self.session.cookies.jar.save()

  def request(
    self, url: str, method: Optional[str] = None, **kwargs,
  ) -> httpx.Response:
    if not self.session:
      self.async_init()

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

    response = self.session.request(method, url, **kwargs) # type: ignore
    # url may have been changed due to redirection
    self.lasturl = str(response.url)
    return response

def test() -> None:
  client = ClientBase(baseurl='https://www.baidu.com/', cookiefile='test')
  res = client.request('/')
  res = client.request('/404')
  print(res, client.lasturl)

if __name__ == '__main__':
  test()
