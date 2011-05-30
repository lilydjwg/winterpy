#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
ard 解码

来源 http://www.wowstory.com/

2011年1月12日
'''

from ctypes import *
from myutils import loadso

_ard = loadso('_ard.so')
_ard.ard.argtypes = (c_char_p,) * 2
_ard.ard.restype = c_char_p

def ard(str1, str2):
  return _ard.ard(str1, str2).decode('utf-8')

