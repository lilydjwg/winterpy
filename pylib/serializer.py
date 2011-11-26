import os
import abc

import pickle

class Serializer(metaclass=abc.ABCMeta):
  def __init__(self, fname, readonly=False, default=None):
    '''
    读取文件fname。readonly指定析构时不回存数据
    如果数据已加锁，将会抛出SerializerError异常
    default 指出如果文件不存在或为空时的数据

    注意：
      要正确地写回数据，需要保证此对象在需要写回时依旧存在，或者使用with语句
      将自身存入其data属性中不可行，原因未知
    '''
    self.fname = os.path.abspath(fname)
    if readonly:
      self.lock = None
    else:
      dir, file = os.path.split(self.fname)
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
            raise SerializerError('数据已加锁')
        open(self.lock, 'w').write(str(os.getpid()))

    try:
      self.load()
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
      self.save()
      os.unlink(self.lock)

  def __enter__(self):
    return self.data

  def __exit__(self, exc_type, exc_value, traceback):
    pass

  @abc.abstractmethod
  def load(self):
    pass

  @abc.abstractmethod
  def save(self):
    pass

class PickledData(Serializer):
  def save(self):
    pickle.dump(self.data, open(self.fname, 'wb'))

  def load(self):
    self.data = pickle.load(open(self.fname, 'rb'))

class SerializerError(Exception): pass

if __name__ == '__main__':
  # For testing purpose
  import tempfile
  f = tempfile.mkstemp()[1]
  testData = {'sky': 1000, 'kernel': -1000}
  try:
    with PickledData(f, default=testData) as p:
      print(p)
      p['space'] = 10000
      print(p)
  finally:
    os.unlink(f)
