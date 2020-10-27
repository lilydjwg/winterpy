from __future__ import annotations

import os
from http.cookiejar import MozillaCookieJar
from urllib.parse import urljoin
from typing import Optional, BinaryIO

import requests

CHUNK_SIZE = 40960

def download_into(session: requests.Session,
                  url: str, file: BinaryIO, process_func=None) -> None:
  r = session.get(url, stream=True)
  length = int(r.headers.get('Content-Length') or 0)
  received = 0
  for chunk in r.iter_content(CHUNK_SIZE):
    received += len(chunk)
    file.write(chunk)
    if process_func:
      process_func(received, length)
  if not length and process_func:
    process_func(received, received)

def download_into_with_progressbar(url, dest):
  import time
  from functools import partial
  from termutils import download_process

  w = os.get_terminal_size()[1]
  with open(dest, 'wb') as f:
    download_into(requests, url, f, partial(
      download_process, dest, time.time(), width=w))

class RequestsBase:
  _session = None
  __our_session: bool = False
  userAgent: Optional[str] = None
  lasturl: Optional[str] = None
  auto_referer: bool = False
  baseurl: Optional[str] = None

  @property
  def session(self):
    if not self._session:
      s = requests.Session()
      if self.userAgent:
        s.headers['User-Agent'] = self.userAgent
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
    self.initialize()

  def initialize(self) -> None:
    '''subclasss can override this to change initialization behavior.'''
    pass

  def __del__(self):
    if self._has_cookiefile:
      self.session.cookies.save()
    if self.__our_session:
      self._session.close()

  def request(self, url: str, method: Optional[str] = None, *args, **kwargs
             ) -> requests.Response:
    if self.baseurl:
      url = urljoin(self.baseurl, url)

    if self.auto_referer and self.lasturl:
      h = kwargs.get('headers', None)
      if not h:
        h = kwargs['headers'] = {}
      h.setdefault('Referer', self.lasturl)

    if method is None:
      if 'data' in kwargs or 'files' in kwargs or 'json' in kwargs:
        method = 'post'
      else:
        method = 'get'

    response = self.session.request(method, url, *args, **kwargs)
    # url may have been changed due to redirection
    self.lasturl = response.url
    return response

if __name__ == '__main__':
  from sys import argv, exit

  if len(argv) != 3:
    exit('URL and output file not given.')

  try:
    download_into_with_progressbar(argv[1], argv[2])
  except KeyboardInterrupt:
    exit(2)
