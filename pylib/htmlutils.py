from __future__ import annotations

import re
import copy
from html.entities import entitydefs

from lxml import html # type: ignore

def _br2span_inplace(el):
  for br in el.iterchildren(tag='br'):
    sp = html.Element('span')
    sp.text = '\n'
    sp.tail = br.tail
    el.replace(br, sp)

def extractText(el):
  el = copy.copy(el)
  _br2span_inplace(el)
  return el.text_content()

def iter_text_and_br(el):
  if el.text:
    yield el.text
  for i in el.iterchildren():
    if i.tag == 'br':
      yield '\n'
    if i.tail:
      yield i.tail

def un_jsescape(s):
    '''%xx & %uxxxx -> char, opposite of Javascript's escape()'''
    return re.sub(
        r'%u([0-9a-fA-F]{4})|%([0-9a-fA-F]{2})',
        lambda m: chr(int(m.group(1) or m.group(2), 16)),
        s
    )

def entityunescape(string):
  '''HTML entity decode'''
  string = re.sub(r'&#[^;]+;', _sharp2uni, string)
  string = re.sub(r'&[^;]+;', lambda m: entitydefs[m.group(0)[1:-1]], string)
  return string

def entityunescape_loose(string):
  '''HTML entity decode. losse version.'''
  string = re.sub(r'&#[0-9a-fA-F]+[;；]?', _sharp2uni, string)
  string = re.sub(r'&\w+[;；]?', lambda m: entitydefs[m.group(0)[1:].rstrip(';；')], string)
  return string

def _sharp2uni(m):
  '''&#...; ==> unicode'''
  s = m.group(0)[2:].rstrip(';；')
  if s.startswith('x'):
    return chr(int('0'+s, 16))
  else:
    return chr(int(s))

def parse_document_from_requests(response, session=None, *, encoding=None):
  '''
  ``response``: requests ``Response`` object, or URL
  ``encoding``: override detected encoding
  '''
  if isinstance(response, str):
    if session is None:
      raise ValueError('URL given but no session')
    r = session.get(response)
  else:
    r = response
  if encoding:
    r.encoding = encoding

  # fromstring handles bytes well
  # https://stackoverflow.com/a/15305248/296473
  parser = html.HTMLParser(encoding=encoding or r.encoding)
  doc = html.fromstring(r.content, base_url=r.url, parser=parser)
  doc.make_links_absolute()

  return doc

def parse_html_with_encoding(data, encoding='utf-8'):
  parser = html.HTMLParser(encoding=encoding)
  return html.fromstring(data, parser=parser)
