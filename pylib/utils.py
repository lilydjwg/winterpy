#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
一些常用短小的函数/类

2010年10月22日
'''

import os, sys

def path_import(path):
  d, f = os.path.split(path)
  if d not in sys.path:
    sys.path[0:0] = [d]
    ret = __import__(os.path.splitext(f)[0])
    del sys.path[0]
    return ret

def filesize(size):
  units = 'KMGT'
  left = size
  unit = -1
  while left > 1100 and unit < 3:
    left = left / 1024
    unit +=1
  if unit == -1:
    return '%dB' % size
  else:
    return '%.1f%siB' % (left, units[unit])
