# vim:fileencoding=utf-8

'''
call external tools to do things.
'''

import os
import re
import subprocess
from functools import lru_cache
from collections import namedtuple

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

PingResult = namedtuple('PingResult', 'loss avg mdev')

def ping(host, *, count=4):
  p = subprocess.Popen(
    ['ping', '-c', str(count), host],
    stdout = subprocess.PIPE)
  out, _ = p.communicate()
  out = out.decode()
  _, loss, stat, _ = out.rsplit('\n', 3)
  loss = re.findall(r'\d+(?=%)', loss)[0]
  loss = float(loss) / 100
  if stat:
    stat = stat.split()[3]
    _, avg, _, mdev = stat.split('/')
  else:
    avg = mdev = -1
  return PingResult(loss, float(avg), float(mdev))

def get_directory_size(d):
  return int(subprocess.check_output(
    ['du', '-sb', d]).decode().split(None, 1)[0])

def get_entropy(input):
  if isinstance(input, bytes):
    stdin = subprocess.PIPE
    data = input
  else:
    stdin = input
    data = None
  p = subprocess.Popen(
    ['ent', '-t'],
    stdin = stdin,
    stdout = subprocess.PIPE,
  )
  out = p.communicate(data)[0].decode()
  header, data = out.splitlines()
  header = header.split(',')[1:]
  data = [float(x) for x in data.split(',')[1:]]
  data[0] = int(data[0])
  return {h: d for h, d in zip(header, data)}

def so_depends(sopath):
  env = os.environ.copy()
  env['LANG'] = env['LC_ALL'] = 'C'
  out = subprocess.check_output(
    ['objdump', '-p', sopath],
    env=env, encoding='utf-8')

  libs = []

  for line in out.splitlines():
    line = line.strip()
    if line.startswith('NEEDED '):
      libs.append(line.split(None, 1)[-1])

  return libs
