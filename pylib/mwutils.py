#!/usr/bin/env python3

import re

def move_category(site, old, new):
  cat = site.pages['Category:' + old]
  pages = cat.members()
  cat_re = re.compile(r'(\[\[:?(?:分类|Category):)%s(\]\])' % re.escape(old))
  for p in pages:
    old_text = p.text()
    text = cat_re.sub(r'\1%s\2' % new.replace('\\', r'\\'), old_text)
    if text == old_text:
      continue
    p.save(text, '分类重命名：[[Category:%s]] -> [[Category:%s]]' % (
      old, new), minor=True)
