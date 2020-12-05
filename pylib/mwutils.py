import re
import logging

import mwclient # type: ignore

logger = logging.getLogger(__name__)

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

def search_and_replace(
  site: mwclient.Site, search: str, regex: re.Pattern, replace: str,
  namespace: int = 0,
) -> None:
  for result in site.search(search, namespace=namespace, what='text'):
    page = site.pages[result['title']]
    text = page.text()
    newtext = regex.sub(replace, text)
    if newtext != text:
      page.edit(newtext, summary=f'replace {regex.pattern} with {replace} (auto)')
      logger.info('page %s updated.', page.page_title)
    else:
      logger.warning('page %s not updated.', page.page_title)
