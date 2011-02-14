#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
与终端相关的工具函数
'''

def green(str):
  return '\x1b[32m%s\x1b[m' % str

def red(str):
  return '\x1b[31m%s\x1b[m' % str

def yellow(str):
  return '\x1b[1;33m%s\x1b[m' % str

