'''
ard 解码

来源 http://www.wowstory.com/

2011年1月12日
'''

from ctypes import *
from myutils import loadso
import sys

_ard = loadso('_ard.so')
_ard.ard.argtypes = (c_char_p,) * 2
_ard.ard.restype = c_char_p

def ard(str1, str2):
  return _ard.ard(str1.encode('utf-8'), str2.encode('utf-8')).decode('utf-8')

if __name__ == '__main__':
  print(ard(sys.argv[1], sys.argv[2]))
