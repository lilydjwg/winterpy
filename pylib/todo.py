#!/usr/bin/env python3
# vim:fileencoding=utf-8

from pickleddata import PData
import random

class TODO:
  def __init__(self, fname):
    self.p = PData(fname)
    if self.p.data is None:
      self.p.data = []
    self.data = self.p.data

  def __call__(self, argv):
    if not argv:
      self.showUsage()
    else:
      cmd = 'do_%s' % argv[0]
      try:
        getattr(self, cmd)(*argv[1:])
      except AttributeError:
        raise NoSuchCommand('命令 %s 没有定义。' % argv[0])
      except TypeError:
        raise CommandError('命令 %s 的参数不正确。' % argv[0])

  def showUsage(self):
    allcmd = sorted(((x[3:], getattr(self, x).__doc__)
        for x in dir(self) if x.startswith('do_')),
        key=lambda x: x[1])
    print('用法：')
    for cmd in allcmd:
      print('\t%s\t%s' % cmd)

  def do_add(self, what, priority=20):
    '''添加新事务（可选优先级）'''
    try:
      priority = int(priority)
    except ValueError:
      raise CommandError('优先级应为整数')

    self.data.append((what, priority))

  def do_get(self):
    '''选取一项事务'''
    allpriority = sum(x[1] for x in self.data)
    try:
      choice = random.randrange(allpriority)
    except ValueError:
      print('没有事务')
      return

    a = 0
    for i in self.data:
      a += i[1]
      if a > choice:
        chosen = i[0]
        break
    print(chosen)

  def do_help(self):
    '''帮助信息'''
    self.showUsage()

class NoSuchCommand(LookupError): pass
class CommandError(Exception): pass

