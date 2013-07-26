# vim:fileencoding=utf-8

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
