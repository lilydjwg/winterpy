#!/usr/bin/env python3
# vim:fileencoding=utf-8

import sys
import re
from email import header
from simplelex import Token, Lex

reply = Token(r'R[Ee]:\s?|[回答][复覆][：:]\s?', 're')
ottag = Token(r'\[OT\]\s?', 'ot', flags=re.I)
tag = Token(r'\[([\w._-]+)[^]]*\]\s?', 'tag')
lex = Lex((reply, ottag, tag))

def decode_multiline_header(s):
  return ''.join(b.decode(e) if e else b for b, e in header.decode_header(re.sub(r'\n\s+', ' ', s)))

def reformat(s):
  tokens, left = lex.parse(s)
  if not tokens:
    return

  isre = False
  tag = None
  ot = False
  usertag = []
  for tok in tokens:
    if tok.idtype == 're':
      isre = True
    elif tok.idtype == 'ot':
      ot = True
    elif tok.idtype == 'tag':
      if tag and tok.match.group(1) != tag[1:-2]:
        usertag.append(tok.data)
      else:
        tag = '[%s] ' % tok.match.group(1)
    else:
      sys.exit('error: unknown idtype: %s' % tok.idtype)

  if isre:
    ret = 'Re: '
  else:
    ret = ''
  if tag:
    ret += tag
  if ot:
    ret += '[OT]'
  ret += ''.join(usertag) + left
  return ret

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
      s = decode_multiline_header(s)
      reformatted = reformat(s)
      if not reformatted:
        yield subject
      else:
        yield 'Subject: ' + header.Header(reformatted, 'utf-8').encode() + '\n'
      subject = None
      yield l
    elif l.strip() == '':
      # mail body
      yield from input
    else:
      yield l

if __name__ == '__main__':
  sys.stdout.writelines(stripSeq(iter(sys.stdin)))
