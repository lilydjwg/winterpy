'''
事件驱动模型

2010年10月22日
'''

import collections

class Event:
  '''所有事件的父类

  stopLater      阻止接下来的同级事件的处理
  stopPropagate  阻止触发父类事件
  preventDefault 阻止默认的处理(与事件同名的方法)
  '''
  stopPropagate = False
  stopLater = False
  preventDefault = False
  def __str__(self):
    return self.__class__.__name__

class EventModel:
  '''事件驱动模型

  listeners  是一个字典，以事件为键，值为一列表
             列表元素为二元组：(函数, 附加的参数)
  listeners2 类似，但是会在默认事件发生之后被处理
  这两个属性通常不需要直接访问。
  '''
  listeners = collections.defaultdict(list)
  listeners2 = collections.defaultdict(list)
  def trigger(self, event):
    ec = event.__class__
    if not issubclass(ec, Event):
      raise TypeError('%s 不是事件的实例' % event)

    for e in ec.__mro__:
      for f in self.listeners[e]:
        f[0](self, event, f[1])
        if event.stopLater:
          break
      # 默认动作
      if not event.preventDefault:
        if hasattr(self, e.__name__):
          getattr(self, e.__name__)(event)
      if not event.stopLater:
        for f in self.listeners2[e]:
          f[0](self, event, f[1])
          if event.stopLater:
            break
      if event.stopPropagate:
        break

  def _checkListener(self, event, func):
    if not issubclass(event, Event):
      raise TypeError('%s 不是事件' % event.__name__)
    if not hasattr(func, '__call__'):
      raise TypeError('func 不是函数')

  def addEventListener(self, event, func, arg):
    self._checkListener(event, func)
    self.listeners[event].append((func, arg))

  def prependEventListener(self, event, func, arg):
    '''将事件添加到最前面'''
    self._checkListener(event, func)
    self.listeners[event].insert(0, (func, arg))

  def appendEventListener(self, event, func, arg):
    '''将事件添加到最后面(后于默认事件)'''
    self._checkListener(event, func)
    self.listeners2[event].append((func, arg))

  def removeEventListener(self, event, func, arg):
    '''移除指定的事件处理器*一次*'''
    self._checkListener(event, func)
    try:
      self.listeners[event].remove((func, arg))
    except ValueError:
      self.listeners2[event].remove((func, arg))

