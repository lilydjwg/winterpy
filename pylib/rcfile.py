'''
跟踪需要备份的配置文件，以 $HOME 为基准目录
'''

import os
import sys

from lilypath import path
from yamlserializer import YAMLData
from termcolor import colored as c
from myutils import getchar
import locale
locale.setlocale(locale.LC_ALL, '')

Ignore = 'ignore'
Normal = 'normal'
Secret = 'secret'
Handled = 'handled'

def cprint(text, color=None, on_color=None, attrs=None, **kwargs):
  print((c(text, color, on_color, attrs)), **kwargs)

class rcfile(YAMLData):
  dirprompt = '%s 是目录。%s' % (c('%s', 'green', attrs=['bold']), c('加入/忽略/已处理/进入/列出文件/tree/Vim/跳过？(y/Y/n/h/e/l/t/v/s) ', 'blue'))
  fileprompt = '%s %s' % (c('%s', 'green', attrs=['bold']), c('加入/忽略/已处理/Vim/跳过？(y/Y/n/h/v/s) ', 'blue'))

  def __init__(self, conffile, readonly=False):
    super().__init__(conffile, readonly=readonly, default={})

  def filelist(self, include=Normal):
    filelist = []

    def parsedir(d, p):
      for k, v in d.items():
        pp = p + k
        if not pp.exists():
          if v != Ignore:
            print('WARNING: %s not found' % pp, file=sys.stderr)
          continue
        if isinstance(v, dict):
          parsedir(v, pp)
        else:
          if v == include:
            filelist.append(pp.value)

    parsedir(self.data, path('~').expanduser())

    return filelist

  def update(self):
    '''交互式更新未纳入管理的文件'''
    startdir = path('~').expanduser()
    oldpwd = os.getcwd()
    if self.data is None:
      self.data = {}
    try:
      self._update(startdir, self.data)
    except KeyboardInterrupt:
      print('已中止。')
    finally:
      os.chdir(oldpwd)

  def _update(self, startdir, data):
    '''implement of self.update, should only be called by it'''
    for f in startdir.list():
      key = f.basename
      if key.endswith('~'):
        continue
      ans = ''
      if isinstance(data.get(key), str):
        continue
      elif isinstance(data.get(key), dict) and data[key]:
        try:
          self._update(f, data[key])
        except OSError as e:
          print(f.value, end=': ')
          cprint(e.strerror, 'red')
        continue
      if f.isdir():
        while not ans:
          ans = getchar(self.dirprompt % f.value)
          if ans == 'y':
            data[key] = Normal
          elif ans == 'Y':
            data[key] = Secret
          elif ans == 'n':
            data[key] = Ignore
          elif ans == 'h':
            data[key] = Handled
          elif ans == 'e':
            data[key] = {}
            try:
              self._update(f, data[key])
            except OSError as e:
              cprint(e.strerror, 'red')
              ans = ''
              continue
          elif ans == 'l':
            try:
              os.chdir(f.value)
            except OSError as e:
              cprint(e.strerror, 'red')
              ans = ''
              continue
            os.system('ls --color=auto')
            ans = ''
          elif ans == 't':
            try:
              os.chdir(f.value)
            except OSError as e:
              cprint(e.strerror, 'red')
              ans = ''
              continue
            os.system('tree -C')
            ans = ''
          elif ans == 'v':
            try:
              os.chdir(f.value)
            except OSError as e:
              cprint(e.strerror, 'red')
              ans = ''
              continue
            os.system("vim .")
            ans = ''
          elif ans == 's':
            continue
          else:
            cprint('无效的选择。', 'red')
            ans = ''
      else:
        while not ans:
          ans = getchar(self.fileprompt % f.value)
          if ans == 'y':
            data[key] = Normal
          elif ans == 'Y':
            data[key] = Secret
          elif ans == 'n':
            data[key] = Ignore
          elif ans == 'h':
            data[key] = Handled
          elif ans == 'v':
            os.system("vim '%s'" % f.value)
            ans = ''
          elif ans == 's':
            continue
          else:
            cprint('无效的选择。', 'red')
            ans = ''

