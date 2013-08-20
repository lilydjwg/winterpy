# vim:fileencoding=utf-8

import re
from email import header

def decode_multiline_header(s):
  ret = []

  for b, e in header.decode_header(re.sub(r'\n\s+', ' ', s)):
    if e:
      if e.lower() == 'gb2312':
        e = 'gb18030'
      b = b.decode(e)
    ret.append(b)

  return ''.join(ret)
