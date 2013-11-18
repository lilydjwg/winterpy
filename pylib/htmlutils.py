# vim:fileencoding=utf-8

import copy

from lxml import html

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

def parse_document_from_requests(url, session, *, encoding=None):
  '''
  ``encoding``: override detected encoding
  '''
  r = session.get(url)
  if encoding:
    r.encoding = encoding

  # fromstring handles bytes well
  # http://stackoverflow.com/a/15305248/296473
  parser = html.HTMLParser(encoding=encoding or r.encoding)
  doc = html.fromstring(r.content, base_url=url, parser=parser)
  doc.make_links_absolute()

  return doc
