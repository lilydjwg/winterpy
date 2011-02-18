#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
让pickle更方便的类，使用它时只需要指定文件即可，不需要记着保存
'''

import pickle
import os

class PData:
  def __init__(self, fname, readonly=False, default=None):
    '''
    读取文件fname。readonly指定析构时不回存数据
    如果数据已加锁，将会抛出PDataError异常
    default 指出如果文件不存在或为空时的数据

    注意：
      要正确地写回数据，需要保证此对象在需要写回时依旧存在，或者使用with语句
      将自身存入其data属性中不可行，原因未知
    '''
    self.fname = os.path.abspath(fname)
    if readonly:
      self.lock = None
    else:
      dir, file = os.path.split(fname)
      self.lock = os.path.join(dir, '.%s.lock' % file)
      for i in (1,):
        # 处理文件锁
        if os.path.exists(self.lock):
          try:
            pid = int(open(self.lock).read())
          except ValueError:
            break

          try:
            os.kill(pid, 0)
          except OSError:
            break
          else:
            self.lock = None
            raise PDataError('数据已加锁')
        open(self.lock, 'w').write(str(os.getpid()))

    try:
      self.data = pickle.load(open(self.fname, 'rb'))
    except EOFError:
      self.data = default
    except IOError as e:
      if e.errno == 2 and not readonly: #文件不存在
        self.data = default
      else:
        raise

  def __del__(self):
    '''如果需要，删除 lock，保存文件'''
    if self.lock:
      pickle.dump(self.data, open(self.fname, 'wb'))
      os.unlink(self.lock)

  def __enter__(self):
    return self.data

  def __exit__(self, exc_type, exc_value, traceback):
    pass

class PDataError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

