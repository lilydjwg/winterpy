'''
Wrapper for tldextract to make managing data easier
'''

import os
import time

from xdg.BaseDirectory import save_cache_path
import tldextract

def extract(url, *, include_psl_private_domains=False):
  cache_dir = save_cache_path('tldextract')
  last_updated = os.path.join(cache_dir, 'last_updated')
  extractor = tldextract.TLDExtract(
    cache_dir = cache_dir,
    include_psl_private_domains = include_psl_private_domains,
  )

  update = False
  try:
    t = os.path.getmtime(last_updated)
    if time.time() - t > 86400 * 7:
      update = True
  except FileNotFoundError:
    update = True

  if update:
    extractor.update()
    with open(last_updated, 'w'): pass

  return extractor(url)

