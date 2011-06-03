#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
简单的分词算法

来源： http://scturtle.is-programmer.com/posts/26648.html
'''

class Fenci:
  def __init__(self, dictfile):
    self.d = {}
    d = self.d
    for line in open(dictfile, encoding='gb18030'):
      word, freq = line.split()
      d[word] = int(freq)

  def __call__(self, string):
    d = self.d
    l = len(string)
    p = [0] * (l+1)
    t = [1] * l
    p[l] = 0
    for i in range(l-1, -1, -1):
      for k in range(1, l-i+1):
        new = d.get(string[i:i+k], 0) + p[i+k]
        if new > p[i]:
          p[i] = new
          t[i] = k
    i = 0
    words = []
    while i < l:
      words.append(string[i:i+t[i]])
      i += t[i]
    return words

if __name__ == '__main__':
  import os
  import sys
  import readline
  print('加载数据...', end='')
  sys.stdout.flush()
  # 词库 http://download.csdn.net/source/347899
  fc = Fenci(os.path.expanduser('~/scripts/python/pydata/dict.txt'))
  print('OK.')
  try:
    while True:
      print(' '.join(fc(input('> '))))
  except (EOFError, KeyboardInterrupt):
    pass
