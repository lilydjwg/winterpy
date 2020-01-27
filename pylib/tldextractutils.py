'''
Wrapper for tldextract to make managing data easier
'''

import os
import time

from xdg.BaseDirectory import save_cache_path
import tldextract

_extractors = {}

def extract(url, *, include_psl_private_domains=False):
  extractor = _extractors.get(include_psl_private_domains)
  if extractor is None:
    if include_psl_private_domains:
      tld_data = os.path.join(
        save_cache_path('tldextract'), 
        'tld_data_psl'
      )
    else:
      tld_data = os.path.join(
        save_cache_path('tldextract'), 
        'tld_data'
      )
    extractor = tldextract.TLDExtract(
      include_psl_private_domains = include_psl_private_domains,
    )
    extractor.cache_file = tld_data
    try:
      t = os.path.getmtime(tld_data)
      if time.time() - t > 86400 * 7:
        extractor.update()
    except FileNotFoundError:
      pass
    _extractors[include_psl_private_domains] = extractor

  return extractor(url)

