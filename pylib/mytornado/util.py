import os
import stat
import datetime

class FileEntry:
  '''For ``StaticFileHandler`` with directory index enabled'''
  isdir = False
  def __init__(self, path, file):
    st = os.stat(os.path.join(path, file))
    self.time = datetime.datetime.fromtimestamp(st[stat.ST_MTIME])
    self.name = file
    self.filename = file
    if stat.S_ISDIR(st[stat.ST_MODE]):
      self.isdir = True
      self.filename += '/'
    self.size = st[stat.ST_SIZE]

  def __lt__(self, another):
    if self.isdir and not another.isdir:
      return True
    if not self.isdir and another.isdir:
      return False
    return self.name < another.name
