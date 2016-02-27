'''For AirDroid 3.2.0'''

import json
import base64
from urllib.parse import quote
from itertools import groupby

from requestsutils import RequestsBase

def url_encode(s):
  return quote(s, safe='')

def base64_encode(s):
  return base64.b64encode(s.encode()).decode('ascii')

class LoginFailed(Exception):
  pass

class AirDroid(RequestsBase):
  def initialize(self):
    if self.baseurl is None:
      raise TypeError('baseurl not set')

  def login(self):
    url = '/sdctl/comm/lite_auth/'
    r = self.request(url)
    ans = r.json()
    # {
    #   "socket_port": 8889,
    #   "port": 8888,
    #   "result": "la_accept",
    #   "7bb": "f146efbd3c24b04c5f0dac74bb460216",
    #   "account_id": "",
    #   "usewifi": true,
    #   "appver": 20148,
    #   "ip": "192.168.1.121",
    #   "unique_id": "191eb19958cbf369bb144e5d51c7ee3f",
    #   "ssl_port": 8890,
    #   "sdkLevel": 19,
    #   "dk": "b5a741c1",
    #   "wss_port": 0,
    #   "account_type": -1
    # }
    if ans['result'] != 'la_accept':
      raise LoginFailed('login failed: %r' % ans)
    self._7bb = ans['7bb']

  def get_phonebook(self):
    url = '/sdctl/requestmany/'
    query = {
      'distinct': False,
      'sortOrder': '_id ASC',
      'projections': '["_id","raw_contact_id","mimetype","data1","data2","data3","data4","data5","data6","data7","data8","data9","data10","data11","data12","data13","data14"]',
      'uri': 'content://com.android.contacts/data',
    }
    params = [{
      "path": "/query/",
      "data": json.dumps(query),
      "isEncode": 0
    }]
    params = json.dumps(params)
    params = url_encode(params)
    params = url_encode(params)
    params = base64_encode(params)
    params = params.replace('=', '%3D')
    params = json.dumps({'content': params})

    r = self.request(
      url,
      params = {
        '7bb': self._7bb,
        'params': params,
      })

    j = r.json()
    # we've sent only one query
    j = j[0]
    data = [list(x) for g, x in groupby(j, key=lambda x: x['raw_contact_id'])]
    mimetype_map = {
      'vnd.android.cursor.item/name': 'name',
      'vnd.android.cursor.item/phone_v2': 'phone',
      'vnd.android.cursor.item/note': 'note',
      'vnd.android.cursor.item/group_membership': '', # not used
      'vnd.android.cursor.item/email_v2': 'email',
    }

    ret = []
    for group in data:
      entry = {}
      for item in group:
        mime = item['mimetype']
        key = mimetype_map.get(mime)
        if key is None:
          raise ValueError('unknown mimetype: %s for data %r' % (
            mime, item))
        elif key == '':
          # ignored
          continue
        entry[key] = item['data1']
        if 'id' not in entry:
          entry['id'] = item['raw_contact_id']
      if entry:
        ret.append(entry)

    return ret
