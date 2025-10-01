import re
import logging
from typing import Optional, Callable
import enum

import mwclient # type: ignore

logger = logging.getLogger(__name__)

CATEGORY_RE = re.compile(r'''
\[\[
  (?P<prefix>(?:分类|Category):)
  (?P<cat>[^]|]+)
  (?P<sorting>\|[^]]+)?
\]\]''', re.VERBOSE)

class Namespace(enum.IntEnum):
  MAIN = 0
  TALK = 1
  USER = 2
  USER_TALK = 3
  PROJECT = 4
  PROJECT_TALK = 5
  FILE = 6
  FILE_TALK = 7
  MEDIAWIKI = 8
  MEDIAWIKI_TALK = 9
  TEMPLATE = 10
  TEMPLATE_TALK = 11
  HELP = 12
  HELP_TALK = 13
  CATEGORY = 14
  CATEGORY_TALK = 15

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
  namespace: Namespace = Namespace.MAIN,
  summary: Optional[str] = None,
  minor: bool = False,
  limit: Optional[int] = None,
  confirm: Optional[Callable[[str, str], bool]] = None,
) -> None:
  count = 0
  if summary is None:
    summary = f'replace {regex.pattern} with {replace} (bot)'
  for result in site.search(search, namespace=namespace.value, what='text'):
    page = site.pages[result['title']]
    text = page.text()
    newtext = regex.sub(replace, text)
    if newtext != text:
      page.edit(newtext, summary=summary, minor=minor)
      logger.info('page %s updated.', page.page_title)
      count += 1
    else:
      logger.warning('page %s not updated.', page.page_title)
    if limit and count >= limit:
      break

def blame(
  site: mwclient.Site,
  revs: list[int],
  revdata: dict[int, str], # revid => text
  needle: str,
) -> int:
  logger.info('blaming in %d revisions for %s', len(revs), needle)

  def get_content(revid: int) -> str:
    if (text := revdata.get(revid)) is None:
      logger.info('fetching content for revid %d', revid)
      rev = site.revisions([revid], prop='timestamp|content')[0]
      text = revdata[revid] = rev['*']
    return text

  new_idx, old_idx = 0, len(revs)-1
  new = get_content(revs[new_idx])
  if needle not in new:
    raise ValueError('needle not found in revs[0]')
  old = get_content(revs[old_idx])
  if needle in old:
    raise ValueError('needle found in revs[-1]')

  while old_idx > new_idx + 1:
    mid_idx = (old_idx + new_idx) // 2
    mid = get_content(revs[mid_idx])
    if needle in mid:
      logger.info('moving to older half')
      new_idx = mid_idx
    else:
      logger.info('moving to newer half')
      old_idx = mid_idx

  return new_idx
