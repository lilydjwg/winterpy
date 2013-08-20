# vim:fileencoding=utf-8

import re
from email import header

def decode_multiline_header(s):
  ret = []

  for b, e in header.decode_header(re.sub(r'\n\s+', ' ', s)):
    if e is None:
      e = 'ascii'
    elif e.lower() == 'gb2312':
      e = 'gb18030'
    ret.append(b.decode(e))

  return ''.join(ret)
