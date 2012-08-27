'''Tools used to calculate and show statistics'''

import math

class Stat:
  '''A class that accepts numbers and provides stats info.

  Available properties are:
  - n: number of numbers that have been added
  - sum: sum
  - avg: average or raise ZeroDivisionError if nothing has been added yet
  - min: mimimum or None if nothing has been added yet
  - max: maximum or None if nothing has been added yet
  - mdev: standard deviation or raise ZeroDivisionError if nothing has been added yet
  - sum2: square sum
  '''
  n = 0
  sum = 0
  sum2 = 0
  min = max = None

  @property
  def avg(self):
    '''average or raise ZeroDivisionError if nothing has been added yet'''
    return self.sum / self.n

  @property
  def mdev(self):
    '''standard deviation or raise ZeroDivisionError if nothing has been added yet'''
    return math.sqrt(self.sum2 / self.n - self.avg ** 2)

  def add(self, x):
    '''add a number to stats'''
    self.n += 1
    self.sum += x
    self.sum2 += x ** 2
    if self.min is None:
      self.min = self.max = x
    else:
      if x < self.min:
        self.min = x
      elif x > self.max:
        self.max = x

  def __str__(self):
    try:
      avg = self.avg
      mdev = self.mdev
      min = self.min
      max = self.max
    except ZeroDivisionError:
      avg = mdev = 0
      min = max = 0
    return 'min/avg/max/mdev = %.3f/%.3f/%.3f/%.3f' % (min, avg, max, mdev)

  def __repr__(self):
    return '<%s.%s: %s>' % (
      self.__class__.__module__,
      self.__class__.__name__,
      self.__str__(),
    )
