#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
更简单的路径处理

lilydjwg <lilydjwg@gmail.com>

2010年11月13日
'''

# 模仿 URL:http://www.jorendorff.com/articles/python/path ver 3.0b1

import os
import sys
from datetime import datetime

__version__ = '0.2'

class path:
  def __init__(self, string='.'):
    self.value = str(string)

  def __str__(self):
    return self.value

  def __repr__(self):
    return '%s(%r)' % (self.__class__.__name__, str(self))

  def __hash__(self):
    st = self.stat()
    return int('%d%d%02d%d' % (st.st_ino, st.st_dev,
        len(str(st.st_ino)), len(str(st.st_dev))))

  def __add__(self, more):
    return self.__class__(self).join(more)

  def __radd__(self, more):
    return self.__class__(self).head(more)

  def __eq__(self, another):
    '''是否为同一文件'''
    return os.path.samefile(self.value, str(another))

  def __contains__(self, another):
    '''another 是否在此路径下'''
    child = os.path.abspath(str(another))
    parent = self.abspath
    if parent == child:
      return True
    if child.startswith(parent) and child[len(parent)] == '/':
      return True
    else:
      return False

  def __lt__(self, another):
    return str.__lt__(str(self), str(another))

  @property
  def abspath(self):
    return os.path.abspath(self.value)

  @property
  def basename(self):
    return os.path.basename(self.value)

  @property
  def rootname(self):
    '''除去扩展名的路径名的 basename'''
    return os.path.splitext(self.basename)[0]

  @property
  def extension(self):
    '''扩展名'''
    return os.path.splitext(self.basename)[1]

  @property
  def realpath(self):
    return os.path.realpath(self.value)

  @property
  def mode(self):
    return self.stat().st_mode

  @property
  def inode(self):
    return self.stat().st_ino

  @property
  def dev(self):
    return self.stat().st_dev

  @property
  def size(self):
    '''以字节表示的文件大小'''
    return self.stat().st_size

  @property
  def atime(self):
    return datetime.fromtimestamp(self.stat().st_atime)
  @property
  def mtime(self):
    return datetime.fromtimestamp(self.stat().st_mtime)
  @property
  def ctime(self):
    return datetime.fromtimestamp(self.stat().st_ctime)
  def stat(self):
    return os.stat(self.value)
  def access(self, mode):
    return os.access(self.value, mode)
  def olderthan(self, another):
    '''比较文件的最后修改时间'''
    if not isinstance(another, path):
      raise TypeError('不能和非 path 对象比较')
    return self.mtime < another.mtime
  def newerthan(self, another):
    return another.olderthan(self)
  def readlink(self):
    return os.readlink(self.value)
  def join(self, *more):
    '''连接路径，使用正确的分隔符'''
    self.value = os.path.join(self.value, *(str(x) for x in more))
    return self

  def head(self, *more):
    '''在路径头部插入，使用正确的分隔符'''
    header = os.path.join(*(str(x) for x in more))
    self.value = os.path.join(header, self.value)
    return self

  def expanduser(self):
    self.value = os.path.expanduser(self.value)
    return self

  def expandvars(self):
    self.value = os.path.expandvars(self.value)
    return self

  def normpath(self):
    self.value = os.path.normpath(self.value)
    return self

  def expand(self):
    '''扩展所有能扩展的，也就是 expanduser 和 expandvars，然后 normpath'''
    self.expanduser().expandvars().normpath()
    return self

  def toabspath(self):
    '''转换为绝对路径'''
    self.value = os.path.abspath(self.value)
    return self

  def torealpath(self):
    '''转换为真实路径'''
    self.value = os.path.realpath(self.value)
    return self

  def islink(self):
    return os.path.islink(self.value)

  def isdir(self):
    return os.path.isdir(self.value)

  def isfile(self):
    return os.path.isfile(self.value)

  def exists(self):
    return os.path.exists(self.value)

  def lexists(self):
    return os.path.lexists(self.value)

  def parent(self):
    '''父目录'''
    return self.__class__(self.value).join('..').normpath()

  def list(self, nameonly=False):
    '''
    路径下所有的东东，如同 os.listdir()，不包含 . 和 ..
    
    nameonly 指定是只返回名字还是返回 path 对象
    '''
    if nameonly:
      return os.listdir(self.value)
    else:
      return [self + self.__class__(x) for x in os.listdir(self.value)]

  def dirs(self, nameonly=False):
    '''路径下所有的目录'''
    if nameonly:
      return [x.basename for x in self.list() if x.isdir()]
    else:
      return [x for x in self.list() if x.isdir()]

  def files(self, nameonly=False):
    '''路径下所有的文件'''
    if nameonly:
      return [x.basename for x in self.list() if x.isfile()]
    else:
      return [x for x in self.list() if x.isfile()]

  def rmdir(self):
    os.rmdir(self.value)
    return self

  def unlink(self, recursive=False):
    '''删除该路径'''
    if self.isdir():
      if recursive:
        for x in self.list():
          x.unlink(True)
      os.rmdir(self.value)
    else:
      os.unlink(self.value)

    return self

  def linksto(self, target, hardlink=False):
    target = str(target)
    if hardlink:
      os.link(target, self.value)
    else:
      os.symlink(target, self.value)

  def mkdir(self, *dirs):
    '''作为目录建立该路径，自动创建上层目录；
    或者在路径下创建目录，要求此路径已经存在。'''
    if dirs:
      if self.exists():
        for d in dirs:
          (self+d).mkdir()
      else:
        raise OSError(2, os.strerror(2), str(self))
    else:
      if self.parent().isdir():
        os.mkdir(str(self))
      elif not self.parent().exists():
        self.parent().mkdir()
        os.mkdir(str(self))
      else:
        raise OSError(17, os.strerror(17), str(self.parent()))

  def rename(self, newname):
    '''文件更名，同时更新本对象所指'''
    os.rename(self.value, newname)
    self.value = newname
    return self

  def copyto(self, newpath):
    '''复制文件，同时更新本对象所指'''
    newpath = self.__class__(newpath)
    if newpath.isdir():
      newpath.join(self.basename)
    import shutil
    shutil.copy2(self.value, newpath.value)
    self.value = newpath.value

  def moveto(self, newpath):
    '''移动文件，同时更新本对象所指'''
    newpath = self.__class__(newpath)
    if newpath.isdir():
      newpath.join(self.basename)
    import shutil
    shutil.move(self.value, newpath.value)
    self.value = newpath.value

  def glob(self, pattern):
    '''返回 list'''
    import glob
    return list(map(path, glob.glob(str(self+pattern))))

  def copy(self):
    '''复制对象并返回之'''
    return self.__class__(self.value)

  def open(self, mode='r', buffering=2, encoding=None, errors=None,
      newline=None, closefd=True):
    '''打开该文件'''
    #XXX 文档说buffering默认值为 None，但事实并非如此。使用full buffering好了
    return open(self.value, mode, buffering, encoding, errors, newline, closefd)

  def traverse(self):
    '''遍历目录'''
    for i in self.list():
      yield i
      if i.isdir():
        for j in i.traverse():
          yield j

class sha1path(path):
  '''使用 sha1 作为文件是否相同的 path'''
  def __eq__(self, another):
    # 先比较文件大小
    if self.size != another.size:
      return False
    return self.sha1() == another.sha1()
  def sha1(self, force=False):
    '''force 为真重读文件'''
    if not hasattr(self, '_sha1') or force:
      import hashlib
      s = hashlib.sha1()
      with self.open('rb') as f:
        while True:
          data = f.read(4096)
          if data:
            s.update(data)
          else:
            break
      self._sha1 = s.hexdigest()
    return self._sha1
