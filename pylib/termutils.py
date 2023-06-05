'''Utilities for CLI programming'''

import os
import sys
import time
from unicodedata import east_asian_width

from myutils import filesize, humantime

def foreach(items, callable, *, process=True, timer=True):
  '''call callable for each item and optionally show a progressbar'''
  if process and timer:
    start_t = time.time()
  n = len(items)

  for i, l in enumerate(items):
    info = callable(i, l)
    if process:
      args = [i+1, n, (i+1)/n*100]
      if info:
        fmt = '%d/%d, %d%% complete [%s]'
        args.append(info)
      else:
        fmt = '%d/%d, %d%% complete...'
      if timer:
        used = time.time() - start_t
        eta = used / (i+1) * (n-i+1)
        fmt = '[ETA: %d Elapsed: %d] ' + fmt
        args = [eta, used] + args

      s = fmt % tuple(args)
      s = '\r' + s + '\x1b[K'
      sys.stderr.write(s)

def download_process(name, startat, got, total, width=80):
  '''Progressbar: [xx%] FileName: yKiB of zMiB, Ts left, sKiB/s'''
  elapsed = time.time() - startat
  speed = got / elapsed
  if got == total:
    # complete
    s1 = 'DONE! '
    fmt2 = ': %s total, %s elapsed, %s/s'
    s2 = fmt2 % (filesize(got), humantime(elapsed), filesize(speed))
  else:
    fmt1 = '[%2d%%] '
    p = got * 100 // total

    fmt2 = ': %s'
    size1 = filesize(got)
    args2 = [size1]
    if total > 0:
      fmt2 += ' of %s'
      args2.append(filesize(total))

      fmt2 += ', %s left, %s/s'
      left = (total - got) / speed
      args2.append(humantime(left))
      args2.append(filesize(speed))

    s1 = fmt1 % p
    s2 = fmt2 % tuple(args2)

  avail = width - len(s1) - len(s2) - 1
  if avail < 0:
    # Sadly, we have too narrow a terminal. Let's output something at least
    avail = 2

  name2 = ''
  for ch in name:
    w = east_asian_width(ch) in 'WF' and 2 or 1
    if avail < w:
      break
    name2 += ch
    avail -= w

  sys.stdout.write('\r' + s1 + name2 + s2 + '\x1b[K')
  if got == total:
    sys.stdout.write('\n')
  else:
    sys.stdout.flush()

