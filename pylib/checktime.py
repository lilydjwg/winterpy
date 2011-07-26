#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
check if any file in a list has been modified or got deleted
'''

import os
import greenlet
 
class TimeChecker(greenlet.greenlet):
  '''
  Initialed with a list of file paths. Later ``switch()`` call will return a changed file list.
  passing in another list to change the file list to be monitored.

  you can access the file list (a tuple) by its property ``filelist``.
  '''
  def __init__(self, filelist):
    super().__init__()
    # outside may not changed this accidentally
    self.filelist = tuple(filelist)
    self.modifyTimes = {}
    self.switch()
 
  def run(self):
    while True:
      result = self.updateTime()
      newlist = self.parent.switch(result)
      if newlist:
        self.modifyTimes = {}
        self.filelist = tuple(newlist)

  def updateTime(self):
    modifyTimes = self.modifyTimes
    modified = []
    for path in self.filelist:
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
