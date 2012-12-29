'''
一些有用的类

2010年10月22日
'''

import datetime
import collections

class StringWithTime(str):
  '''包含时间信息的字符串'''
  def __init__(self, value, time=None):
    str.__init__(self)
    if time is None:
      time = datetime.datetime.now()
    self.time = time

  def __repr__(self):
    return '<"%s" at "%s">' % ( self, self.time.strftime('%Y/%m/%d %H:%M:%S'))

class ListBasedSet(collections.Set):
  ''' Alternate set implementation favoring space over speed
      and not requiring the set elements to be hashable. '''
  def __init__(self, iterable=()):
    self.elements = lst = []
    for value in iterable:
      if value not in lst:
        lst.append(value)
  def __iter__(self):
    return iter(self.elements)
  def __contains__(self, value):
    return value in self.elements
  def __len__(self):
    return len(self.elements)

class StrlikeList(list):
  '''多个非重复数据
  add 用于添加数据项'''

  def __init__(self, iterable, maxlength=0, formatter=None):
    '''formatter 用于输出字符串表示
    maxlength 为最大长度，0 为不限制'''
    list.__init__(self, iterable)
    if formatter is None:
      formatter = lambda x: ', '.join(x)
    self.formatter = formatter
    self.maxlength = maxlength

  def __str__(self):
    return self.formatter(self)

  def add(self, item):
    if item in self:
      self.remove(item)
    self.insert(0, item)
    ml = self.maxlength
    if ml and len(self) > ml:
      del self[ml:]

