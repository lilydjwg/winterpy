#!/usr/bin/env python3
# fileencoding=utf-8

'''
从 fcitx码表导出文件 转换成极点五笔码表文件
'''

import os
import struct, io
from datetime import datetime

class jdmb:
  def __init__(self, infile, outfile):
    self.infname = infile
    self.outfile = open(outfile, 'wb')

  def run(self):
    self.header()
    self.header2()
    self.main()
    self.doIndex()

  def header(self):
    h = '百合五笔小企鹅输入法词库%s版 for 极点五笔UniCode版本\r\n生成日期:%s'
    h = h % (datetime.fromtimestamp(os.path.getmtime(self.infname)).strftime('%Y%m%d'),
        datetime.today().strftime('%Y-%m-%d %H:%M'))

    self.outfile.write(b'Freeime Dictionary V5.0')
    self.outfile.write(h.encode('utf-16le'))
    self.outfile.write(b'\x00'*(0xe7 - self.outfile.tell()))
    self.outfile.write(b'\x01')
    self.outfile.write(b'\x00'*(0x11f - self.outfile.tell()))
    self.outfile.write(b'\x1a')

  def header2(self):
    h = 'abcdefghijklmnopqrstuvwxyzz'.encode('utf-16le')
    h = h + (0x56 - len(h)) * b'\x00'
    self.outfile.write(h)

    h = 'p11+p21+p31+p32'.encode('utf-16le')
    h = h + (0x3e - len(h)) * b'\x00'
    self.outfile.write(h)

    self.outfile.write(b'z\x00z\x00')

  def main(self):
    '''将主体数据存到 self.maindata'''
    self.maindata = io.BytesIO()
    found = False
    index = [[['A', 0]], [['AA', 0]], [['AAA', 0]]]
    for l in open(self.infname):
      if not found:
        if l == '[数据]\n':
          found = True
        continue
      d = l.rstrip('\n').split(' ')
      # 索引用
      try:
        if d[0][0] != index[0][-1][0][0]:
          index[0].append([d[0], self.maindata.tell()])
        if d[0][1] and d[0][:2] != index[1][-1][0][:2]:
          index[1].append([d[0], self.maindata.tell()])
        if d[0][2] and d[0][:3] != index[2][-1][0][:3]:
          index[2].append([d[0], self.maindata.tell()])
      except IndexError:
        pass
      d[0] = d[0].encode('ascii')
      d[1] = d[1].encode('utf-16le')
      e = struct.pack('<3B', len(d[0]), len(d[1]), 0x64)
      self.maindata.write(e)
      self.maindata.write(d[0] + d[1])
    del index[0][0]
    del index[1][0]
    del index[2][0]
    self.index = index

  def doIndex(self):
    chars = 'abcdefghijklmnopqrstuvwxyz'
    cursor = 0
    # 单字母索引
    for i in chars:
      try:
        if self.index[0][cursor][0] == i:
          b = struct.pack('<I', self.index[0][cursor][1] + 0x1b620)
          self.outfile.write(b)
          cursor += 1
        else:
          self.outfile.write(b'\xff\xff\xff\xff')
      except IndexError:
        self.outfile.write(b'\xff\xff\xff\xff')

    bichars = [i+j for i in chars for j in chars]
    cursor = 0
    for i in bichars:
      try:
        if self.index[1][cursor][0][:2] == i:
          b = struct.pack('<I', self.index[1][cursor][1] + 0x1b620)
          self.outfile.write(b)
          cursor += 1
        else:
          self.outfile.write(b'\xff\xff\xff\xff')
      except IndexError:
        self.outfile.write(b'\xff\xff\xff\xff')

    trichars = [i+j+k for i in chars for j in chars for k in chars]
    cursor = 0
    for i in trichars:
      try:
        if self.index[2][cursor][0][:3] == i:
          b = struct.pack('<I', self.index[2][cursor][1] + 0x1b620)
          self.outfile.write(b)
          cursor += 1
        else:
          self.outfile.write(b'\xff\xff\xff\xff')
          # print(i, self.index[2][cursor][0][:3])
      except IndexError:
        self.outfile.write(b'\xff\xff\xff\xff')

    hw = 0x1b620 - self.outfile.tell()
    self.outfile.write(b'\xff'*hw)
    self.maindata.seek(0)
    b = self.maindata.read(1024)
    while b:
      self.outfile.write(b)
      b = self.maindata.read(1024)

def test():
  '''测试用'''
  a = jdmb('lily', 'freeime.mb')
  a.header()
  a.header2()
  a.main()
  a.doIndex()
  return a

if __name__ == '__main__':
  import sys
  if len(sys.argv) == 3:
    jd = jdmb(*sys.argv[1:])
    jd.run()
  else:
    print('用法： jdmb.py fcitx码表导出文件 输出文件')
    sys.exit(1)

