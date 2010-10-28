#!/usr/bin/env python3
# vim:fileencoding=utf-8

from xml.dom import *

def getText(el):
  ch = el.childNodes
  if not ch:
    return ''

  ret = []

  for e in ch:
    type = e.nodeType
    if type == Node.TEXT_NODE:
      ret.append(e.nodeValue)
    elif type == Node.ELEMENT_NODE:
      ret.append(getText(e))
    else:
      raise NotImplementedError('type is %d' % type)

  return ''.join(ret)

def setText(el, text):
  del el.childNodes[:]
  tn = el.ownerDocument.createTextNode(text)
  el.appendChild(tn)
