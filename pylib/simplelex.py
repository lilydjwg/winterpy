# modified version, originally from 风间星魂 <fengjianxinghun AT gmail>
# BSD Lisence

import re
from collections import UserString

_RE_Pattern = re.compile('').__class__

class Token:
  '''useful attributes: pattern, idtype'''
  def __init__(self, pat, idtype=None, flags=0):
    self.pattern = pat if isinstance(pat, _RE_Pattern) else re.compile(pat, flags)
    self.idtype = idtype

  def __repr__(self):
    return '<%s: pat=%r, idtype=%r>' % (
      self.__class__.__name__,
      self.pattern.pattern, self.idtype)

class TokenResult(UserString):
  '''useful attributes: match, token, idtype'''
  def __init__(self, string, match, token):
    self.data = string
    self.token = token
    self.match = match
    self.idtype = token.idtype

class Lex:
  '''first matching token is taken'''
  def __init__(self, tokens=()):
    self.tokens = tokens

  def parse(self, string):
    ret = []
    while len(string) > 0:
      for p in self.tokens:
        m = p.pattern.match(string)
        if m is not None:
          ret.append(TokenResult(m.group(), match=m, token=p))
          string = string[m.end():]
          break
      else:
        break
    return ret, string

def main():
  s = 'Re: [Vim-cn] Re: [Vim-cn:7166] Re: 回复：[OT] This is the subject.'
  reply = Token(r'R[Ee]:\s?|[回答]复[：:]\s?', 're')
  ottag = Token(r'\[OT\]\s?', 'ot', flags=re.I)
  tag = Token(r'\[([\w._-]+)[^]]*\]\s?', 'tag')

  lex = Lex((reply, ottag, tag))
  tokens, left = lex.parse(s)
  print('tokens:', tokens)
  print('left:', left)

if __name__ == '__main__':
  main()
