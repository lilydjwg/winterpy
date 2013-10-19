#!/usr/bin/env python
# vim:fileencoding=utf-8

'''
OpenCC wrapper

Tested with OpenCC version 0.4.2, 0.4.3.
Compatile with both Python 2.x and 3.x.
'''

from __future__ import print_function

from ctypes import cdll, c_char_p
import readline
import sys

if sys.version_info < (3,):
    def input(prompt=''):
        return raw_input(prompt).decode('utf-8')

    def bytes(name, encoding):
        return str(name)

__all__ = ['OpenCC']

try:
    libopencc = cdll.LoadLibrary('libopencc.so')
except OSError:
    libopencc = cdll.LoadLibrary('libopencc.so.1')
libc = cdll.LoadLibrary('libc.so.6')

class OpenCC(object):
    def __init__(self, config_file):
        self.od = libopencc.opencc_open(c_char_p(bytes(config_file, 'utf-8')))
        if self.od == -1:
            raise Exception('failed to create an OpenCC object')

    def convert(self, text):
        text = text.encode('utf-8')
        retv_c = c_char_p(libopencc.opencc_convert_utf8(self.od, text, len(text)))
        ret = retv_c.value.decode('utf-8')
        libc.free(retv_c)
        return ret

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('config file not provided.')

    converter = OpenCC(sys.argv[1])
    while True:
        try:
            l = input()
            print(converter.convert(l))
        except (EOFError, KeyboardInterrupt):
            break
