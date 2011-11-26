'''
XML 相关的小工具函数
'''

import re
from lxml.html import parse, etree, tostring, fromstring

allen = re.compile(r'^[\x20-\x7f]+$')
en = re.compile(r'[\x20-\x7f]+')

def enText(doc):
  doc.set('lang', 'zh-CN')
  for el in doc.xpath('//p|//dt|//dd|//li|//a|//span|//em|//h2|//h3|//strong'):
    if el.getparent().tag == 'pre':
      continue
    if el.getparent().get('role') == 'pre':
      continue
    text = el.text
    if text:
      text = text.strip()
      if not allen.match(text) or el.getchildren():
        ms = list(en.finditer(text))
        for i, m in enumerate(ms):
          span = etree.Element('span')
          span.set('lang', 'en')
          span.text = m.group(0)
          el.insert(i, span)
          if i == 0:
            el.text = text[:m.start()]
          try:
            span.tail = text[m.end():ms[i+1].start()]
          except IndexError:
            span.tail = text[m.end():]
      else:
        el.set('lang', 'en')

  for el in doc.xpath('//a|//span|//em|//code|//strong'):
    if el.getparent().tag == 'pre':
      continue
    text = el.tail
    if text:
      text = text.strip()
      ms = list(en.finditer(text))
      for i, m in enumerate(ms):
        span = etree.Element('span')
        span.set('lang', 'en')
        span.text = m.group(0)
        tail = el.tail
        el.addnext(span)
        # re-insert mispositioned tail; the previous one will be overwritten
        el.tail = tail
        if i == 0:
          el.tail = text[:m.start()]
        el = span
        try:
          el.tail = text[m.end():ms[i+1].start()]
        except IndexError:
          el.tail = text[m.end():]

def enText_convert(oldfile, newfile):
  doc = fromstring(open(oldfile).read())
  enText(doc)
  with open(newfile, 'w') as f:
    f.write(doc.getroottree().docinfo.doctype + '\n')
    f.write(tostring(doc, encoding=str, method='xml'))

if __name__ == '__main__':
  import sys
  if len(sys.argv) == 3:
    enText_convert(*sys.argv[1:])
  else:
    print('parameters: old_file new_file', file=sys.stderr)
