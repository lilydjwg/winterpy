#!/usr/bin/env python3
# vim:fileencoding=utf-8

try:
  import vim
except ImportError:
  raise RuntimeError('This module should only use inside Vim')

def viminput(prompt='', style=None):
  if style is not None:
    vim.command('echohl %s' % style)
  ans = vim.eval("input('%s')" % prompt.replace("'", "''"))
  if style is not None:
    vim.command('echohl None')
  return ans

def vimprint(style, text):
  vim.command("echohl %s | echo '%s' | echohl None" % (style, text.replace("'", "''")))

def addtovim():
  vim.input = viminput
  vim.print = vimprint

addtovim()
del viminput, vimprint
