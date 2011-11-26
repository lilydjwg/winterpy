try:
  import vim
except ImportError:
  raise RuntimeError('This module should only use inside Vim')

def input(prompt='', style=None):
  if style is not None:
    vim.command('echohl %s' % style)
  ans = vim.eval("input('%s')" % prompt.replace("'", "''"))
  if style is not None:
    vim.command('echohl None')
  return ans

def print(style, text):
  vim.command("echohl %s | echo '%s' | echohl None" % (style, text.replace("'", "''")))
