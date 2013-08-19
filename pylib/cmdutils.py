# vim:fileencoding=utf-8

'''
call external tools to do things.
'''

import subprocess
from functools import lru_cache

@lru_cache(maxsize=20)
def lookupip(ip, cmd='cip'):
  return subprocess.getoutput(subprocess.list2cmdline([cmd, ip])).replace('CZ88.NET', '').strip() or '-'
