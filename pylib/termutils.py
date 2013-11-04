'''Utilities for CLI programming'''

import sys
import time

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

