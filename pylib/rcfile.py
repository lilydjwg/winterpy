#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
跟踪需要备份的配置文件

文件格式说明：
  最顶层的路径是目录位置，支持 ~ 扩展
'''

import os

from path import path
from yamlserializer import YAMLData
from termcolor import colored as c
from myutils import getchar
import locale
locale.setlocale(locale.LC_ALL, '')

def cprint(text, color=None, on_color=None, attrs=None, **kwargs):
  print((c(text, color, on_color, attrs)), **kwargs)

class rcfile(YAMLData):
  dirprompt = '%s 是目录。%s' % (c('%s', 'green', attrs=['bold']), c('加入/忽略/进入/列出文件/tree/Vim/跳过？(y/Y/n/e/l/t/v/s) ', 'blue'))
  fileprompt = '%s %s' % (c('%s', 'green', attrs=['bold']), c('加入/忽略/Vim/跳过？(y/Y/n/v/s) ', 'blue'))

  def __init__(self, conffile, readonly=False):
    super().__init__(conffile, readonly=readonly, default={})

  def filelist(self, include=1):
    filelist = []

    def parsedir(d, p):
      for k, v in d.items():
        if isinstance(v, dict):
          parsedir(v, p+k)
        else:
          if v == include:
            filelist.append((p+k).value)

    for k, v in self.data.items():
      if v is not None:
        p = path(k).expanduser()
        parsedir(v, p)

    return filelist

  def update(self, startdir):
    '''交互式更新未纳入管理的文件'''
    data = self.data[startdir]
    if data is None:
      data = self.data[startdir] = {}
    startdir = path(startdir).expanduser()
    oldpwd = os.getcwd()
    try:
      self._update(startdir, data)
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
      if isinstance(data.get(key), int):
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
            data[key] = 1
          elif ans == 'Y':
            data[key] = 2
          elif ans == 'n':
            data[key] = 0
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
            os.system("vim '%s'" % key)
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
            data[key] = 1
          elif ans == 'Y':
            data[key] = 2
          elif ans == 'n':
            data[key] = 0
          elif ans == 'v':
            os.system("vim '%s'" % f.value)
            ans = ''
          elif ans == 's':
            continue
          else:
            cprint('无效的选择。', 'red')
            ans = ''

  def updateAll(self):
    for d in self.data:
      self.update(d)

  def new(self, path):
    self.data[path] = None
    self.update(path)

