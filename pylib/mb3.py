#!/usr/bin/env python3
# vim:fileencoding=utf-8:sw=2

'''操作 fcitx 的码表文件（第三版，针对UTF-8版）'''
import sys
import struct
import algorithm

version = 0.3

# 测试/调试设置
# msg = True
msg = False
timeit = True

if msg and timeit:
  from datetime import datetime

class Record:
  '''一条记录'''
  def __init__(self, code, hz, hit=0, index=0, ispy=False):
    self.code = code
    self.hz = hz
    self.hit = hit
    self.index = index
    self.ispy = ispy

  def __lt__(self, x):
    return self.code < x.code

  def __eq__(self, x):
    return self.code == x.code and self.hz == x.hz

  def __le__(self, x):
    return self < x or self.code == x.code

  def __repr__(self):
    '''表示法，与输出到文本文件时一致（除了<>）'''
    if self.ispy:
      f = '<@{0.code} {0.hz} {0.hit} {0.index}>'
    else:
      f = '<{0.code} {0.hz} {0.hit} {0.index}>'
    return f.format(self)

  def __str__(self):
    return '[{0.code}:{0.hz}]'.format(self)

  def toString(self, verbose=False):
    '''输出到文本文件时用'''
    if verbose:
      f = '{0.code} {0.hz} {0.hit} {0.index}'
    else:
      f = '{0.code} {0.hz}'
    if self.ispy:
      f = '@' + f
    return f.format(self)

  def update(self, ref=None, code=None, hz=None, hit=0, index=0, ispy=False):
    '''更新数据，根据 ref 或者手动指定值'''
    if not any((code, hz, hit, index, ispy)):
      if ref:
        self.code = ref.code
        self.hz = ref.hz
        self.hit = ref.hit
        self.index = ref.index
        self.ispy = ref.ispy
      else:
        raise TypeError('参数过少。')
    else:
      if code:
        self.code = code
      if hz:
        self.hz = hz
      if hit:
        self.hit = hit
      if index:
        self.index = index
      if ispy:
        self.ispy = ispy

class mbTable:
  '''小企鹅输入法码表对象'''
  # TODO 在不用此对象时释放内存
  文件名 = None
  版本 = None
  键码 = None
  码长 = None
  规避字符 = ''
  拼音长度 = None
  组词规则 = None
  数据 = []
  编码 = set()
  modified = False

  def __getitem__(self, i):
    '''可以直接通过下标访问某个编码的数据'''
    return self.数据[i]

  def __delitem__(self, i):
    '''也可以直接通过下标来删除'''
    del self.数据[i]

  def __init__(self, file=None):
    '''初始化对象，可选从某个文件载入
或者以后手动通过 self.load 从字符串载入'''
    # 将文件全部读入。希望这个文件不会太大。
    # 如果以后逐步读取的话会更花时间
    self.文件名 = file
    if file:
      data = open(file, 'rb').read()
      self.load(data)

  def __repr__(self):
    return '<小企鹅输入法码表对象，来自文件 “%s”。>' % self.文件名

  def __str__(self):
    '''这个码表的信息'''
    return '''版本：{版本}
键码：{键码}
码长：{码长}
规避字符：{规避字符}
拼音长度：{拼音长度}
组词规则：{组词规则}
数据：{数据} 条
修改过（不一定可靠）：{modified}'''.format(版本=self.版本,
        键码=self.键码,
        码长=self.码长,
        规避字符=self.规避字符,
        拼音长度=self.拼音长度,
        组词规则=self.组词规则,
        数据=self.size(),
        modified=self.modified,
    )


  def autoCode(self, hz):
    '''自动生成词的编码'''
    # 造词一次测试用时 0.26+ 秒
    if not self.组词规则:
      raise self.autoCodeError('组词失败，因为当前码表没有组词规则可用')

    for i in self.组词规则:
      if (i[0] == 'e' and int(i[1]) == len(hz)) or (i[0] == 'a'
          and len(hz) >= int(i[1])):
        break
    else:
      raise self.autoCodeError('组词失败，因为没有找到对长度为 %d 的词的组词规则' % len(hz))

    if msg:
      print('自动造词...')
      if timeit:
        imeitstart = datetime.today()
    a = i[3:].split('+')
    c = ''
    for j in a:
      # 分析一次测试用时 0.06x 秒
      longestHere = -1
      if msg:
        print('分析组词规则...')
        if timeit:
          timeitstart = datetime.today()
      if j[0] == 'p': # 正序
        zx = True
      elif j[0] == 'n': # 逆序
        zx = False
      else:
        raise self.autoCodeError('不能识别的组词规则 %s' % i)
      if zx:
        字 = hz[int(j[1])-1]
      else:
        字 = hz[-int(j[1])]
      # 找出最长的编码；五笔有简码的
      longest = 0
      for i in self.search(字):
        length = len(self[i].code)
        if length > longest:
          longest = length
          longestHere = i
      if msg:
        print('分析完毕。')
        if timeit:
          print('用时', datetime.today() - timeitstart)
      try:
        if longestHere == -1:
          raise self.autoCodeError('组词失败，因为我没能找到“%s”的编码' % 字)
        c += self.数据[longestHere].code[int(j[2])-1]
      except IndexError:
        raise self.autoCodeError('组词失败，因为“%s”的编码太短了' % 字)

    if msg:
      print('自动造词完毕。')
      if timeit:
        print('用时', datetime.today() - imeitstart)
    return c

  def delete(self, code=None, hz=None):
    '''删除指定项，返回删除的条数'''
    count = 0

    # 按编码
    if code and not hz:
      pos = self.getpos(code)
      while self.数据[pos].code == code:
        del self.数据[pos]
        count += 1
        # pos = self.getpos(code)
      if count: self.modified = True
      return count

    # 按编码和汉字
    # 也可以用 remove，不过这样似乎快一点
    if code and hz:
      pos = self.getpos(code)
      while self.数据[pos].code == code:
        if self.数据[pos].hz == hz:
          count += 1
          del self.数据[pos]
          # 假设没有重复项
          break
        pos += 1
      if count: self.modified = True
      return count

    # 只按汉字
    if hz:
      pos = self.search(hz)
      for i in pos:
        # 删一个就少一个
        del self.数据[i-count]
        count += 1
      if count: self.modified = True
      return count

    raise self.argsError('code 和 hz 至少要指明一项')

  def get(self, record):
    '''
    获取 record 以便修改
    
    record 是 Record 对象
    '''
    pos = self.getpos(record)
    try:
      while self.数据[pos].code == record.code:
        # 注意到虽然编码排序了，但汉字部分并没有排序
        if self.数据[pos] == record:
          return self.数据[pos]
        else:
          pos += 1
    except IndexError:
      pass
    raise self.RecordNotExist(record)

  def getpos(self, record):
    '''获取 record 的位置。如果它不存在，获取它应当被插入的位置
    
record 可以是 Record 对象或者表示编码的字符串'''
    if isinstance(record, Record):
      return algorithm.二分搜索(self.数据, record)
    else:
      return algorithm.二分搜索(self.数据, record, (lambda x, y: x > y.code))

  def getbycode(self, code):
    '''获取 code 对应的数据'''
    pos = self.getpos(code)
    ret = []
    try:
      while self.数据[pos].code == code:
        ret.append(self.数据[pos])
        pos += 1
    except IndexError:
      pass

    return ret

  def gethz(self, code):
    '''获取 code 对应的汉字'''
    pos = self.getpos(code)
    ret = []
    try:
      while self.数据[pos].code == code:
        ret.append(self.数据[pos].hz)
        pos += 1
    except IndexError:
      pass

    return ret

  def getsimilar(self, code, similar=1):
    '''寻找相似的编码（相似度小于等于 similar 者）'''
    # 测试用时 (查询编码的长度).x 秒

    # 列出所有编码
    # 测试用时 0.0x 秒
    if msg:
      print('查询相似编码...')
      if timeit:
        imeitstart = datetime.today()
    if not self.编码:
      if msg:
        print('生成编码集合...')
        if timeit:
          timeitstart = datetime.today()
      for i in self.数据:
        self.编码.add(i.code)
      if msg:
        print('编码集合生成完毕。')
        if timeit:
          print('用时', datetime.today() - timeitstart)

    ret = []
    for i in self.编码:
      if algorithm.LevenshteinDistance(code, i) <= similar:
        ret.append(i)

    if msg:
      print('相似编码查询完毕。')
      if timeit:
        print('用时', datetime.today() - imeitstart)
    return ret 

  def insert(self, code, hz, hit=0, index=0, ispy=False):
    '''插入记录'''
    if not self.maybeCode(code):
      raise self.argsError('不符合当前码表编码的格式')

    t = Record(code, hz, hit, index, ispy)
    try:
      self.get(t)
      # 已经存在
      raise self.RecordExists(t)
    except self.RecordNotExist:
      self.数据.insert(self.getpos(t), t)
      self.modified = True

  def load(self, data):
    '''
    从字符串载入数据

    此字符串应该来源于码表文件
    通常不需要手动调用此方法
    '''
    start = 0

    # 载入码表属性测试用时 0.001x 秒
    # 版本号
    fmt = '<I'
    size = 4
    x = struct.unpack(fmt, data[:size])[0]
    start += size
    if x:
      self.版本 = 2
    else:
      fmt = '<B'
      size = 1
      self.版本 = struct.unpack(fmt, data[start:start+size])[0]
      start += size

    # 键码字串
    fmt = '<I'
    size = 4
    x = struct.unpack(fmt, data[start:start+size])[0]
    start += size
    fmt = '<' + str(x+1) + 's'
    size = struct.calcsize(fmt)
    self.键码 = struct.unpack(fmt, data[start:start+size])[0][:-1].decode('utf-8')
    start += size

    # 码长
    fmt = '<B'
    size = 1
    self.码长 = struct.unpack(fmt, data[start:start+size])[0]
    start += size

    # 拼音长度
    if self.版本:
      fmt = '<B'
      size = 1
      self.拼音长度 = struct.unpack(fmt, data[start:start+size])[0]
      start += size

    # 规避字符
    fmt = '<I'
    size = 4
    x = struct.unpack(fmt, data[start:start+size])[0]
    start += size
    fmt = '<' + str(x+1) + 's'
    size = struct.calcsize(fmt)
    self.规避字符 = struct.unpack(fmt, data[start:start+size])[0][:-1].decode('utf-8')
    start += size

    # 组词规则
    fmt = '<B'
    size = 1
    x = struct.unpack(fmt, data[start:start+size])[0]
    start += size
    if x: # 有组词规则
      self.组词规则 = [''] * (self.码长-1)
      for i in range(self.码长-1):
        fmt = '<BB'
        size = 2
        x = struct.unpack(fmt, data[start:start+size])
        start += size
        if x[0]:
          self.组词规则[i] = 'a'
        else:
          self.组词规则[i] = 'e'
        self.组词规则[i] += str(x[1])
        self.组词规则[i] += '='
        for j in range(self.码长):
          fmt = '<BBB'
          size = 3
          x = struct.unpack(fmt, data[start:start+size])
          start += size
          if x[0]:
            self.组词规则[i] += 'p'
          else:
            self.组词规则[i] += 'n'
          self.组词规则[i] += str(x[1])
          self.组词规则[i] += str(x[2])
          if j != self.码长 - 1:
            self.组词规则[i] += '+'

    # 词的数量
    fmt = '<I'
    size = 4
    x = struct.unpack(fmt, data[start:start+size])[0]
    start += size

    if msg:
      print('载入数据中...')
      if timeit:
        timeitstart = datetime.today()
    # 读数据了
    # 测试用时近两秒
    # XXX 如果没有 版本？
    if self.版本:
      fmt2 = '<' + str(self.拼音长度+1) + 's'
    size2 = struct.calcsize(fmt2)
    for i in range(x):
      # 键码
      fmt = fmt2
      size = size2
      x = struct.unpack(fmt, data[start:start+size])[0]
      try:
        code = x[:x.find(b'\x00')].decode('utf-8')
      except UnicodeDecodeError:
        return
      start += size
      # 汉字
      fmt = '<I'
      size = 4
      x = struct.unpack(fmt, data[start:start+size])[0]
      start += size
      fmt = '<' + str(x) + 's'
      size = struct.calcsize(fmt)
      hz = struct.unpack(fmt, data[start:start+size])[0][:-1].decode('utf-8')
      start += size

      ispy = False
      if self.版本:
        # 拼音指示
        fmt = '<B'
        size = 1
        x = struct.unpack(fmt, data[start:start+size])[0]
        start += size
        if x:
          ispy = True

      # 词频信息
      fmt = '<II'
      size = 8
      x = struct.unpack(fmt, data[start:start+size])
      start += size
      hit = x[0]
      index = x[1]

      # 添加一个记录
      self.数据.append(Record(code, hz, hit, index, ispy))
    if msg:
      print('数据载入完成。')
      if timeit:
        print('用时', datetime.today() - timeitstart)

  def loadFromTxt(self, txtfile, encoding='utf-8'):
    '''从导出的纯文本文件中导入（不建议使用！）

适用于在导出修改后的情况，这时不要载入码表文件
注意：不保证对所有情况适用
      数据部分必须排序

因C++版的程序由于算法有问题导致重复项，考虑导出修改后再导入而写'''

    import re
    with open(txtfile, encoding=encoding) as txt:
      self.版本 = int(re.search(r'0x\d{2}', txt.readline()).group(0), 16)
      l = txt.readline().rstrip()
      self.键码 = l[l.find('=')+1:]
      l = txt.readline().rstrip()
      self.码长 = int(l[l.find('=')+1:])
      txt.readline()
      l = txt.readline().rstrip()
      self.拼音长度 = int(l[l.find('=')+1:])
      l = txt.readline().rstrip()
      if l == '[组词规则]':
        self.组词规则 = []
        l = txt.readline().rstrip()
        while l != '[数据]':
          self.组词规则.append(l)
          l = txt.readline().rstrip()
      if l == '[数据]':
        l = txt.readline()
        while l:
          l = l.split(' ') # 以英文空格分隔，不含全角空格
          if l[0].startswith('@'):
            self.数据.append(Record(l[0][1:], l[1], int(l[2]), int(l[3]), True))
          else:
            self.数据.append(Record(l[0], l[1], int(l[2]), int(l[3])))
          l = txt.readline()

      self.modified = True

  def maybeCode(self, string):
    '''string 可能是合法的编码吗？'''
    if len(string) > self.码长:
      return False
    for i in string:
      if i not in self.键码:
        return False
    return True

  def print(self, 文件=None, 词频=False, 编码='utf-8'):
    '''以纯文本方式输出
    
如果词频为 False 并且编码为默认的话，所得文件与 mb2txt 程序产生的
完全一致'''

    # 不打印词频时测试用时 2.5x 秒
    # 打印词频时测试用时 2.7x 秒
    if 文件:
      f = open(文件, 'w', encoding=编码)
    else:
      f = sys.stdout

    # 打印码表属性 0.0003x 秒
    print(';fcitx 版本', '0x%02x' % self.版本, '码表文件', file=f)
    print('键码='+self.键码, file=f)
    print('码长=%d' % self.码长, file=f)
    if self.拼音长度:
      print('拼音=@', file=f)
      print('拼音长度=%d' % self.拼音长度, file=f)
    if self.规避字符:
      print('规避字符=' + self.规避字符, file=f)
    if self.组词规则:
      print('[组词规则]', file=f)
      for i in self.组词规则:
        print(i, file=f)
    if msg:
      print('打印数据...')
      if timeit:
        timeitstart = datetime.today()
    print('[数据]', file=f)
    lastcode = ''
    tmpRecords = []
    for i in self.数据 :
      if i.code == lastcode:
        tmpRecords.append(i)
      elif tmpRecords:
        tmpRecords.sort(key=lambda x: -x.index)
        for j in tmpRecords:
          print(j.toString(词频), file=f)
        lastcode = i.code
        tmpRecords = [i]
      else:
        lastcode = i.code
        tmpRecords = [i]
    if msg:
      print('打印数据完成。')
      if timeit:
        print('用时', datetime.today() - timeitstart)

  def save(self):
    '''保存到原文件'''
    self.write(self.文件名)

  def search(self, hz, 搜寻子串=False):
    '''寻找汉字，返回索引列表，搜寻子串 指示是否要准确匹配
    
返回结果总是排序过的'''
    # 精确匹配时测试用时 0.06x 秒
    # 模糊匹配时测试用时 0.1x 秒
    if msg:
      print('查询汉字...')
      if timeit:
        timeitstart = datetime.today()
    ret = []
    if not 搜寻子串:
      for i in range(len(self.数据)):
        if self.数据[i].hz == hz:
          ret.append(i)
    else:
      for i in range(len(self.数据)):
        if self.数据[i].hz.find(hz) != -1:
          ret.append(i)
    if msg:
      print('汉字查询完成。')
      if timeit:
        print('用时', datetime.today() - timeitstart)
    return ret

  def set(self, code, hz, hit=0, index=0, ispy=False):
    '''插入或设置词频信息'''
    # 这个和 insert 方法的有点重复了
    if not self.maybeCode(code):
      raise self.argsError('不符合当前码表编码的格式')

    t = Record(code, hz, hit, index, ispy)
    try:
      self.get(t).update(t)
      self.modified = True
    except self.RecordNotExist:
      # 不存在
      self.insert(code, hz, hit, index, ispy)

  def size(self):
    '''数据的条数'''
    return len(self.数据)

  __len__ = size

  def write(self, 文件, 保留词频信息=True):
    '''保存到文件'''
    # 测试用时 3.6x 秒
    f = open(文件, 'wb')

    # 写入属性测试用时 0.0006+ 秒
    # 版本号
    fmt = '<I'
    if self.版本:
      f.write(struct.pack(fmt, 0))
      fmt = '<B'
      f.write(struct.pack(fmt, self.版本))
    else:
      f.write(struct.pack(fmt, 1))

    # 键码字串
    fmt = '<I'
    x = self.键码.encode('utf-8')
    f.write(struct.pack(fmt, len(x)))
    fmt = '<' + str(len(x)) + 'sB'
    f.write(struct.pack(fmt, x, 0))

    # 码长
    fmt = '<B'
    f.write(struct.pack(fmt, self.码长))

    # 拼音长度
    if self.版本:
      fmt = '<B'
      f.write(struct.pack(fmt, self.拼音长度))

    # 规避字符
    fmt = '<I'
    x = self.规避字符.encode('utf-8')
    f.write(struct.pack(fmt, len(x)))
    fmt = '<' + str(len(x)) + 'sB'
    f.write(struct.pack(fmt, x, 0))

    # 组词规则
    if self.组词规则: # 有组词规则
      fmt = '<B'
      f.write(struct.pack(fmt, 7))
      for i in range(self.码长-1):
        if self.组词规则[i][0] == 'e':
          f.write(struct.pack(fmt, 0))
        else:
          f.write(struct.pack(fmt, 1))
        f.write(struct.pack(fmt, int(self.组词规则[i][1])))
        for j in range(self.码长):
          x = 3 + j * 4
          if self.组词规则[i][x] == 'n':
            f.write(struct.pack(fmt, 0))
          else:
            f.write(struct.pack(fmt, 1))
          f.write(struct.pack(fmt, int(self.组词规则[i][x+1])))
          f.write(struct.pack(fmt, int(self.组词规则[i][x+2])))
    else:
      f.write(struct.pack(fmt, 0))

    # 词的数量
    fmt = '<I'
    f.write(struct.pack(fmt, self.size()))

    if msg:
      print('写入数据中...')
      if timeit:
        timeitstart = datetime.today()
    # 写数据了
    if self.版本:
      size = self.拼音长度 + 1
    fmt2 = '<' + str(size) + 's'
    for i in self.数据:
      x = i.code.encode('utf-8').ljust(size, b'\x00')
      y = i.hz.encode('utf-8') + b'\x00'
      # 键码
      fmt = fmt2
      f.write(struct.pack(fmt, x))
      # 汉字
      fmt = '<I'
      f.write(struct.pack(fmt, len(y)))
      fmt = '<' + str(len(y)) + 's'
      f.write(struct.pack(fmt, y))
      # 拼音指示
      if self.版本:
        fmt = '<B'
        if i.ispy:
          f.write(struct.pack(fmt, 1))
        else:
          f.write(struct.pack(fmt, 0))
      # 词频信息
      fmt = '<II'
      f.write(struct.pack(fmt, i.hit, i.index))

    f.close()
    if msg:
      print('文件写入完成。')
      if timeit:
        print('用时', datetime.today() - timeitstart)
    self.modified = False

  class argsError(Exception):
    '''mb 的错误类：参数值不符合要求'''

    def __init__(self, value):
      self.value = value
    def __str__(self):
      return repr(self.value)

  class autoCodeError(Exception):
    '''mb 的错误类：自动生成编码失败'''

    def __init__(self, value):
      self.value = value
    def __str__(self):
      return repr(self.value)

  class RecordExists(Exception):
    '''mb 的错误类：插入时编码已经存在'''
    def __init__(self, value):
      self.value = value
    def __str__(self):
      return repr(self.value)+' 已经存在'

  class RecordNotExist(Exception):
    '''mb 的错误类：参数值不符合要求'''

    def __init__(self, value):
      self.value = value
    def __str__(self):
      return repr(self.value)+' 不存在'

