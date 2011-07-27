#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
check if any file in a set has been modified or got deleted
'''

import os

class TimeChecker:
  '''
  Initialed with a set of file paths. Later ``check()`` call will return a changed file list.
  passing in another set to change the file set to be monitored.

  you can access the file set (a frozenset) by its property ``fileset``.
  '''
  def __init__(self, fileset):
    # outside may not changed this accidentally
    self.fileset = frozenset(fileset)
    self.modifyTimes = {}
    self.check()

  def check(self, newlist=None):
    result = self.updateTime()
    if newlist:
      self.modifyTimes = {}
      self.fileset = frozenset(newlist)
    return result

  def updateTime(self):
    modifyTimes = self.modifyTimes
    modified = []
    for path in self.fileset:
      try:
        modify_time = os.stat(path).st_mtime
      except OSError:
        if path in modifyTimes:
          del modifyTimes[path]
          modified.append(path)
        continue
      if path not in modifyTimes:
        modifyTimes[path] = modify_time
        continue
      if modifyTimes[path] != modify_time:
        modifyTimes[path] = modify_time
        modified.append(path)
    return modified
