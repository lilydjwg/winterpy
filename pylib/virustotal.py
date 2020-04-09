from typing import Tuple, Optional, Dict, Any
import asyncio

from aiohttp import FormData
from aiohttputils import ClientBase

Json = Dict[str, Any]

class VirusTotalError(Exception):
  def __init__(self, code: str, message: str) -> None:
    self.code = code
    self.message = message

  def __repr__(self) -> str:
    clsname = self.__class__.__name__
    return f'<{clsname}: {self.code}: {self.message}>'

def _get_stats(j: Json, key: str) -> Tuple[int, int]:
  stat = j['data']['attributes'][key]
  return (stat['malicious'] + stat['suspicious'],
          stat['undetected'] + stat['harmless'])

def _check_error(j: Json) -> None:
  if 'error' in j:
    e = j['error']
    raise VirusTotalError(e['code'], e['message'])

class VirusTotal(ClientBase):
  baseurl: str = 'https://www.virustotal.com/api/v3/'

  def __init__(self, apikey: str) -> None:
    self.apikey = apikey
    super().__init__()

  async def api_request(self, path: str, **kwargs) -> Json:
    res = await self.request(path, headers = {
      'x-apikey': self.apikey,
    }, **kwargs)
    j = await res.json()
    _check_error(j)
    return j

  async def check_hash(self, hash: str) -> Optional[Tuple[int, int]]:
    try:
      j = await self.api_request(f'files/{hash}')
    except VirusTotalError as e:
      if e.code == 'NotFoundError':
        return None
      raise
    return _get_stats(j, 'last_analysis_stats')

  async def submit_file(
    self, content: bytes, filename: str,
  ) -> str:
    data = FormData()
    data.add_field(
      'file', content,
      filename = filename,
      content_type = 'application/octet-stream',
    )
    j = await self.api_request('files', data=data)
    _check_error(j)
    return j['data']['id']

  async def check_bytes(
    self, content: bytes, filename: str,
  ) -> Tuple[int, int]:
    aid = await self.submit_file(content, filename)

    while True:
      j = await self.api_request(f'analyses/{aid}')
      _check_error(j)
      if j['data']['attributes']['status'] == 'queued':
        await asyncio.sleep(5)
      else:
        break

    return _get_stats(j, 'stats')
