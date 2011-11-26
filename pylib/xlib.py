'''
X11 相关工具
'''

from ctypes import *
from myutils import loadso

_xlib = loadso('_xlib.so')
_xlib.test_display.argtypes = (c_char_p,)

def test_display(name):
  return bool(_xlib.test_display(name.encode('utf-8')))

