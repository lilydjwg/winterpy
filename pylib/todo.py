import sqlite3
import os
import sys

class TODO:
  def __init__(self, fname):
    self.conn = sqlite3.connect(fname)
    self.cursor = self.conn.cursor()
    self.setup()

  def __del__(self):
    self.cursor.close()
    self.conn.commit()
    self.conn.close()

  def __call__(self, argv):
    if not argv:
      self.do_last()
    else:
      cmd = 'do_%s' % argv[0]
      try:
        getattr(self, cmd)(*argv[1:])
      except AttributeError:
        raise NoSuchCommand('命令 %s 没有定义。' % argv[0])
      except TypeError:
        raise CommandError('命令 %s 的参数不正确。' % argv[0])

  def setup(self):
    sql = '''create table if not exists item (
      id integer primary key autoincrement,
      what text not null)'''
    self.cursor.execute(sql)
    sql = '''create table if not exists info (
      name text primary key not null,
      value text not null)'''
    self.cursor.execute(sql)

  def showUsage(self):
    allcmd = sorted(((x[3:], getattr(self, x).__doc__)
        for x in dir(self) if x.startswith('do_')),
        key=lambda x: x[0])
    print('用法：')
    for cmd in allcmd:
      print('\t%s\t%s' % cmd)

  def edit(self, init=None):
    fname = '/tmp/todo_list'
    editor = os.environ['EDITOR'] or 'vim'
    try:
      if init:
        open(fname, 'w').write(init)
      os.system('%s %s' % (editor, fname))
      what = open(fname).read().rstrip()
      os.unlink(fname)
    except IOError:
      print('未找到编辑过的文件，中断。', file=sys.stderr)
      return
    return what

  def getlast(self):
    sql = '''select value from info where name = 'last_id' '''
    self.cursor.execute(sql)
    for c in self.cursor:
      id = int(c[0])

    sql = '''select what from item where id = %d''' % id
    self.cursor.execute(sql)
    what = ''
    for c in self.cursor:
      what = c[0]

    return id, what

  def update(self, id, what):
    '''添加新事务'''
    sql = '''update item set what=? where id=%d''' % id
    self.cursor.execute(sql, (what,))

  def do_vi(self):
    '''使用文本编辑器编辑新事务'''
    what = self.edit()
    if what:
      self.do_add(what)

  def do_edit(self):
    '''使用文本编辑器编辑最后的事务'''
    id, last = self.getlast()
    what = self.edit(last)
    if what:
      self.update(id, what)

  def do_add(self, what):
    '''添加新事务'''
    sql = '''insert into item (what) values (?)'''
    self.cursor.execute(sql, (what,))

  def do_last(self):
    '''显示最后被选择的项'''
    what = self.getlast()[1]
    print(what)

  def do_count(self):
    '''事务总数'''
    sql = '''select count(*) from item'''
    self.cursor.execute(sql)
    for c in self.cursor:
      howmany = c[0]
    print('共 %d 项事务' % howmany)

  def do_del(self):
    '''删除最后被选择的项'''
    sql = '''delete from item where id in (
      select value from info where name = 'last_id')'''
    self.cursor.execute(sql)

  def do_get(self):
    '''选取一项事务'''
    sql = '''select id, what from item where id != %d order by random() limit 1''' % self.getlast()[0]
    self.cursor.execute(sql)
    for c in self.cursor:
      id, what = c
      break
    else:
      print('没有事务')
      return
    sql = '''insert or replace into info (name, value)
      values ('last_id', '%d')''' % id
    self.cursor.execute(sql)
    print(what)

  def do_help(self):
    '''帮助信息'''
    self.showUsage()

class NoSuchCommand(LookupError): pass
class CommandError(Exception): pass
