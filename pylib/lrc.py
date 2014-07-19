'''
A simple lrc file parser
'''

import re

_sep_re = re.compile(r'[\[\]]+')
_time_re = re.compile(r'(\d+):(\d+)(?:.(\d+))?')

def parse(s):
  lines = s.split('\n')
  ret = meta, texts = {}, []
  for l in lines:
    l = l.strip()
    if not l:
      continue
    type, info = parse_line(l)
    if type == 'header':
      meta[info[0]] = info[1]
    else:
      texts.extend(info)
  return ret

def parse_line(l):
  *tags, text = _sep_re.split(l)[1:]
  ret = []
  type = 'time'
  for tag in tags:
    m = _time_re.match(tag)
    if not m:
      type = 'header'
      ret = tags[0], text
      break
    g = m.groups()
    t = int(g[0]) * 60 + int(g[1]) + (int(g[2]) / 100 if g[2] else 0.0)
    ret.append((t, text))
  return type, ret

def uniq(timed_text):
  last_text = None
  ret = []
  for time, text in timed_text:
    if last_text != text:
      ret.append((time, text))
    last_text = text
  return ret

def sort(timed_text):
  return sorted(timed_text, key=lambda x: x[0])

if __name__ == '__main__':
  from pprint import pprint
  import sys
  for f in sys.argv[1:]:
    print(f, ':', sep='')
    t = open(f).read()
    r = parse(t)
    r = r[0], uniq(sort(r[1]))
    pprint(r)
    print()
