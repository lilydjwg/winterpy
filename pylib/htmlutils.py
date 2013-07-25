# vim:fileencoding=utf-8

import sys
import time
import copy

import lxml.html

def _br2span_inplace(el):
  for br in el.iterchildren(tag='br'):
    sp = lxml.html.Element('span')
    sp.text = '\n'
    sp.tail = br.tail
    el.replace(br, sp)

def extractText(el):
  el = copy.copy(el)
  _br2span_inplace(el)
  return el.text_content()

def foreach(links, callable, *, process=True, timer=True):
  if process and timer:
    start = time.time()
  n = len(links)

  for i, l in enumerate(links):
    info = callable(i, l)
    if process:
      if info:
        fmt = '\r%d/%d complete [%s]'
        args = [i+1, n, info]
      else:
        fmt = '\r%d/%d complete...'
        args = [i+1, n]
      if timer:
        used = time.time() - start
        eta = used / (i+1) * (n-i+1)
        fmt = '\r[ETA: %d Used: %d] ' + fmt[1:]
        args = [eta, used] + args

      sys.stderr.write(fmt % tuple(args))
