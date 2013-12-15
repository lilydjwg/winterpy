# vim:fileencoding=utf-8

'''
call external tools to do things.
'''

import subprocess
from functools import lru_cache

@lru_cache(maxsize=20)
def lookupip(ip, cmd='cip'):
  return subprocess.getoutput(subprocess.list2cmdline([cmd, ip])).replace('CZ88.NET', '').strip() or '-'

def check_mediafile(file):
  '''intergrity check with ffmpeg

  also return ``False`` when reading the file fails

  From http://superuser.com/a/100290/40869
  '''

  p = subprocess.Popen(
    ['ffmpeg', '-v', 'error', '-i', file, '-f', 'null', '-'],
    stderr = subprocess.PIPE)
  _, e = p.communicate()
  return not bool(e.strip())
