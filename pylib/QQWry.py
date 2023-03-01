#!/usr/bin/env python3

'''QQWry 模块，提供读取纯真IP数据库的数据的功能。

纯真数据库格式参考 https://web.archive.org/web/20140423114336/http://lumaqq.linuxsir.org/article/qqwry_format_detail.html
作者 AutumnCat. 最后修改在 2008年 04月 29日
bones7456 最后修改于 2009-02-02
lilydjwg 修改于 2014-05-26
lilydjwg 再次修改于 2019-01-02
本程序遵循 GNU GENERAL PUBLIC LICENSE Version 2 (http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt)
'''

from struct import unpack, pack
import sys
import socket, mmap
from collections import namedtuple
import re
import os
import zlib
import subprocess
import tempfile
import shutil
from typing import Tuple

from myutils import safe_overwrite

DataFileName = os.path.expanduser('~/etc/data/QQWry.Dat')

copywrite_url = 'http://update.cz88.net/ip/copywrite.rar'
data_url = 'http://update.cz88.net/ip/qqwry.rar'

def _ip2ulong(ip):
  '''点分十进制 -> unsigned long
  '''
  return unpack('>L', socket.inet_aton(ip))[0]

def _ulong2ip(ip):
  '''unsigned long -> 点分十进制
  '''
  return socket.inet_ntoa(pack('>L', ip))

def _extract_date(s):
    return tuple(int(x) for x in re.findall(r'\d+', s))

class IpInfo(namedtuple('IpInfo', 'sip eip country area')):
  def __str__(self):
    '''str(x)
    '''
    # TODO: better formatting
    return str(self[0]).ljust(16) + ' - ' + str(self[1]).rjust(16) + ' ' + self[2] + self[3]

  def normalize(self):
    '''转化ip地址成点分十进制.
    '''
    return self.__class__(
      _ulong2ip(self[0]), _ulong2ip(self[1]), self[2], self[3])

class QQWry:
  def __init__(self, dbfile=DataFileName, charset='gbk'):
    self.charset = charset
    with open(dbfile, 'rb') as dbfile:
      self.f = mmap.mmap(dbfile.fileno(), 0, access=mmap.MAP_SHARED)
    self.indexBaseOffset = unpack('<L', self.f[0:4])[0] #索引区基址
    self.count = (unpack('<L', self.f[4:8])[0]
                  - self.indexBaseOffset) // 7 # 索引数-1

  def Lookup(self, ip: str) -> IpInfo:
    '''x.Lookup(ip) -> (sip, eip, country, area) 查找 ip 所对应的位置.

    ip, sip, eip 是点分十进制记录的 ip 字符串.
    sip, eip 分别是 ip 所在 ip 段的起始 ip 与结束 ip.
    '''
    return self._n_lookup(_ip2ulong(ip))

  def _n_lookup(self, ip: int) -> IpInfo:
    '''x._n_lookup(ip) -> (sip, eip, country, area) 查找 ip 所对应的位置.

    ip 是 unsigned long 型 ip 地址.
    其它同 x.Lookup(ip).
    '''
    si = 0
    ei = self.count
    if ip < self._readIndex(si)[0]:
      raise LookupError('IP not found.')
    elif ip >= self._readIndex(ei)[0]:
      si = ei
    else: # keep si <= ip < ei
      while (si + 1) < ei:
        mi = (si + ei) // 2
        if self._readIndex(mi)[0] <= ip:
          si = mi
        else:
          ei = mi
    ipinfo = self[si]
    if ip > ipinfo[1]:
      raise LookupError('IP not found.')
    else:
      return ipinfo

  def __str__(self):
    tmp = []
    tmp.append('RecCount:')
    tmp.append(str(len(self)))
    tmp.append('\nVersion:')
    tmp.extend(self[self.count].normalize()[2:])
    return ''.join(tmp)

  def __len__(self):
    return self.count + 1

  def __getitem__(self, key):
    '''x[key]

    若 key 为整数, 则返回第key条记录(从0算起, 注意与 x._n_lookup(ip) 不一样).
    若 key 为点分十进制的 ip 描述串, 同 x.Lookup(key).
    '''
    if isinstance(key, int):
      if key >= 0 and key <= self.count:
        index = self._readIndex(key)
        sip = index[0]
        pos = index[1]
        eip = unpack('<L', self.f[pos:pos+4])[0]
        country, area = self._readRec(pos+4)
        if area == ' CZ88.NET':
          area = ''
        return IpInfo(sip, eip, country, area)
      else:
        raise IndexError
    elif isinstance(key, str):
      return self.Lookup(key).normalize()
    else:
      raise TypeError('key must be str or int')

  def _read3ByteOffset(self, pos: int) -> int:
    data = self.f[pos:pos+3] + b'\x00'
    return unpack('<L', data)[0]

  def _read_cstring(self, start: int) -> Tuple[str, int]:
    if start == 0:
      return 'Unknown', start + 1

    end = self.f.find(b'\x00', start)
    if end < 0:
      raise Exception('fail to read C string')
    data = self.f[start:end]
    return data.decode(self.charset, errors='replace'), end + 1

  def _readIndex(self, n: int) -> Tuple[int, int]:
    pos = self.indexBaseOffset + 7 * n
    data = self.f[pos:pos+7] + b'\x00'
    ip, offset = unpack('<LL', data)
    return ip, offset

  def _readRec(self, pos: int, *, onlyOne=False):
    f = self.f
    mode = f[pos]
    if mode == 0x01:
      rp = self._read3ByteOffset(pos+1)
      result = self._readRec(rp, onlyOne=onlyOne)
    elif mode == 0x02:
      rp = self._read3ByteOffset(pos+1)
      result = self._readRec(rp, onlyOne=True)
      if not onlyOne:
        result.append(self._readRec(pos+4, onlyOne=True)[0])
    else: # string
      s, new_pos = self._read_cstring(pos)
      result = [s]
      if not onlyOne:
        result.append(self._readRec(new_pos, onlyOne=True)[0])

    return result

  def getDate(self):
    return _extract_date(self[self.count].area)

MQQWry = QQWry

def decipher_data(key, data):
  h = bytearray()
  for b in data[:0x200]:
    key *= 0x805
    key += 1
    key &= 0xff
    h.append(key ^ b)
  return bytes(h) + data[0x200:]

def unpack_meta(data):
  # http://microcai.org/2014/05/11/qqwry_dat_download.html
  sign, version, _1, size, _, key, text, link = \
      unpack('<4sIIIII128s128s', data)
  sign = sign.decode('gb18030')
  text = text.rstrip(b'\x00').decode('gb18030')
  link = link.rstrip(b'\x00').decode('gb18030')
  del data
  return locals()

def update(q):
  # no longer available; check here instead:
  # https://github.com/zu1k/nali/blob/master/pkg/qqwry/qqwry.go
  # https://99wry.cf/qqwry.dat
  try:
    tmp_dir = tempfile.mkdtemp(prefix='QQWry')
    old_d = os.getcwd()
    try:
      Q = QQWry()
    except OSError as e:
      print('注意：原数据文件无法打开：', e, file=sys.stderr)
      Q = None
    os.chdir(tmp_dir)

    wget = ['wget', '-4', '-U', 'Mozilla/3.0 (compatible; Indy Library)']
    if q:
      wget.append('-q')
    subprocess.run(wget + [copywrite_url], check=True)
    with open('copywrite.rar', 'rb') as f:
      d = f.read()
    info = unpack_meta(d)
    date = _extract_date(info['text'])
    if Q and date <= Q.getDate():
      if not q:
        print(info['text'], '是最新的！', file=sys.stderr)
      return
    else:
      if q != 2:
        print(info['text'], '开始下载...', file=sys.stderr, flush=True)
    p = subprocess.Popen(['wget', '-4', '-U', 'Mozilla/3.0 (compatible; Indy Library)', data_url])
    p.wait()
    d = open('qqwry.rar', 'rb').read()
    d = decipher_data(info['key'], d)
    d = zlib.decompress(d)

    os.chdir(old_d)
    safe_overwrite(DataFileName, d, mode='wb')
    old_c = Q and Q.count or 0
    Q = QQWry()
    if q != 2:
      print('已经更新！数据条数 %d->%d.' % (old_c, Q.count), file=sys.stderr)
  finally:
    shutil.rmtree(tmp_dir)

def main():
  import argparse
  parser = argparse.ArgumentParser(description='纯真IP数据库查询与更新')
  parser.add_argument('IP', nargs='*',
                      help='要查询的IP')
  parser.add_argument('-u', '--update', action='store_true', default=False,
                      help='更新数据库')
  parser.add_argument('-a', '--all', action='store_true', default=False,
                      help='输出所有IP数据')
  parser.add_argument('-q', '--quiet', action='store_true', default=False,
                      help='更新数据库时，没有更新则不输出内容')
  parser.add_argument('-Q', '--more-quiet', action='store_true', default=False,
                      help='更新数据库时总是不输出内容')

  args = parser.parse_args()

  if args.update:
    q = 0
    if args.more_quiet:
      q = 2
    elif args.quiet:
      q = 1
    update(q)
    return

  Q = QQWry()
  if args.all:
    try:
      for i in Q: #遍历示例代码
        print(i.normalize())
    except IOError:
      pass
    return

  ips = args.IP
  if not ips:
    print(Q)
  elif len(ips) == 1:
    if ips[0] == '-': #参数只有一个“-”时，从标准输入读取IP
      print(''.join(Q[input()][2:]))
    else: #参数只有一个IP时，只输出简要的信息
      print(' '.join(Q[sys.argv[1]][2:]))
  else:
    for i in ips:
      print(Q[i])

if __name__ == '__main__':
  main()
