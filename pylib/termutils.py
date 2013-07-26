'''Utilities for CLI programming'''

import sys
import time

def foreach(items, callable, *, process=True, timer=True):
  '''call callable for each item and optionally show a progressbar'''
  if process and timer:
    start = time.time()
  n = len(items)

  for i, l in enumerate(items):
    info = callable(i, l)
    if process:
      if info:
        fmt = '%d/%d complete [%s]'
        args = [i+1, n, info]
      else:
        fmt = '%d/%d complete...'
        args = [i+1, n]
      if timer:
        used = time.time() - start
        eta = used / (i+1) * (n-i+1)
        fmt = '[ETA: %d Used: %d] ' + fmt
        args = [eta, used] + args

      s = fmt % tuple(args)
      s = '\r' + s + '\x1b[K'
      sys.stderr.write(s)

