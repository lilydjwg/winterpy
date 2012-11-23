#!/usr/bin/env python3
# vim:fileencoding=utf-8

import sys
import re
from email import header

subject_seq = re.compile(r'''(..[:：]\s?  # Re、回复等
                             \[[^:]+)
                             :\d+         # 要删除的序号''', re.X)

def stripSeq(input):
  subject = None
  while True:
    l = next(input)
    if l.startswith('Subject: '):
      # Subject appears
      subject = l
      continue
    elif subject and l[0] in ' \t':
      # Subject continues
      subject += l
    elif subject:
      # Subject ends
      s = subject[9:]
      h = header.decode_header(s)
      assert len(h) == 1, 'unexpected subject line: ' + s
      s, enc = h[0]
      if isinstance(s, bytes):
        s = s.decode(enc)
      m = subject_seq.match(s)
      if not m:
        yield subject
      else:
        s = m.group(1) + s[m.end():]
        yield 'Subject: ' + header.Header(s, 'utf-8').encode() + '\n'
      subject = None
    elif l.strip() == '':
      # mail body
      yield from input
    else:
      yield l

if __name__ == '__main__':
  sys.stdout.writelines(stripSeq(iter(sys.stdin)))
