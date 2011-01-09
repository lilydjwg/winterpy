#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
XML 相关的小工具函数

2011年1月9日
'''

from lxml import etree
import re
allen = re.compile(r'^[\x20-\x7f]+$')
en = re.compile(r'[\x20-\x7f]+')

def enText(doc):
  doc.xpath('//body')[0].attrib['lang'] = 'zh'
  for el in doc.xpath('//p|//dt|//dd|//li|//a|//span|//em|//h2|//h3'):
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

  for el in doc.xpath('//a|//span|//em|//code'):
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
        el.addnext(span)
        if i == 0:
          el.tail = text[:m.start()]
        el = span
        try:
          el.tail = text[m.end():ms[i+1].start()]
        except IndexError:
          el.tail = text[m.end():]

def enText_convert(oldfile, newfile):
  doc = etree.parse(oldfile)
  enText(doc)
  doc.write(newfile, encoding='UTF-8', xml_declaration=True)
