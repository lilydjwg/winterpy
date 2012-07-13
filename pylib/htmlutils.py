# vim:fileencoding=utf-8

import lxml.html

def br2eol(el):
  for br in el.iterchildren(tag='br'):
    sp = lxml.html.Element('span')
    sp.text = '\n'
    sp.tail = br.tail
    el.replace(br, sp)
