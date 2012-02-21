#!/usr/bin/env python3
# vim:fileencoding=utf-8

import sys
import json
import urllib.request

from url import PostData

def translate(text):
  post = {
    'from': 'jp',
    'to': 'zh',
    'ie': 'utf-8',
    'source': 'txt',
    'query': text,
  }
  ans = urllib.request.urlopen('http://fanyi.baidu.com/transcontent', PostData(post).data).read().decode('utf-8')
  result = json.loads(ans)
  return result['data'][0]['dst']

if __name__ == '__main__':
  if len(sys.argv) == 2:
    print(translate(sys.argv[1]))
  elif len(sys.argv) == 1:
    print(translate(sys.stdin.read()))
  else:
    sys.exit('what to translate?')
