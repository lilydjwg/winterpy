from collections import namedtuple

import requests

SongInfo = namedtuple(
    'SongInfo',
    'sid name href artists album extra')

class Base:
  _session = None
  userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:25.0) ' \
          'Gecko/20100101 Firefox/25.0'

  def __init__(self, session=None):
    self._session = session

  @property
  def session(self):
    if not self._session:
      s = requests.Session()
      s.headers['User-Agent'] = self.userAgent
      self._session = s
    return self._session

