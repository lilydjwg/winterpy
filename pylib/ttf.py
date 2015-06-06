'''read ttf info'''

import struct
from chardet import detect

class TTF:
  def __init__(self, filename):
    self.filename = filename
    self.file = open(filename, 'rb')

    # 文件头信息
    self.file.seek(0)
    header = self.file.read(12)
    self.MajorVersion, self.MinorVersion, self.NumOfTables, \
        self.SearchRange, self.EntrySelector, self.RangeShift = \
        struct.unpack('>6H', header)
    self.tables = {} # 存放表的数据用

  def readTableDirectory(self, offset):
    '''从 offset 处读一个表的数据'''
    self.file.seek(offset)
    data = self.file.read(16)
    name, checksum, dataOffset, length = struct.unpack('>4s3L', data)
    name = name.decode('ascii')
    return name, checksum, dataOffset, length

  def getnameinfo(self):
    '''找到并读取 name 表'''
    tableinfo = self.readTableDirectory(12)
    count = 1
    while tableinfo[0] != 'name' and count <= self.NumOfTables:
      tableinfo = self.readTableDirectory(12+count*16)
      count += 1
    if count > self.NumOfTables:
      raise ValueError('name 表没有找到！')

    self.file.seek(tableinfo[2])
    data = self.file.read(tableinfo[3])
    number, stringStart = struct.unpack('>3H', data[0:6])[1:]
    info = []
    for i in range(number-1):
      offset = 6 + i * 12
      info.append(struct.unpack('>6H', data[offset:offset+12]))
    nameinfo = {}
    data = data[stringStart:]
    for i in info:
      rawstring = struct.unpack('>%ds' % i[4],
            data[i[5]:i[4]+i[5]])[0]
      # TODO 根据给出编码来解码
      # encoding = i[2]
      if b'\x00' in rawstring:
        thestring = rawstring.decode('utf-16be')
      else:
        encoding = detect(rawstring)['encoding']
        if not encoding:
          encoding = 'latin1'
        thestring = rawstring.decode(encoding)
      # 调试用
      # thestring = thestring, rawstring

      if i[3] == 0:
        nameinfo['copyright'] = thestring
      elif i[3] == 1:
        nameinfo['name'] = thestring
      elif i[3] == 2:
        nameinfo['subname'] = thestring
      elif i[3] == 3:
        nameinfo['id'] = thestring
      elif i[3] == 4:
        nameinfo['fullname'] = thestring
      elif i[3] == 5:
        nameinfo['version'] = thestring
      elif i[3] == 6:
        nameinfo['psname'] = thestring
      elif i[3] == 7:
        nameinfo['trademark'] = thestring
    return nameinfo

  def __del__(self):
    self.file.close()

