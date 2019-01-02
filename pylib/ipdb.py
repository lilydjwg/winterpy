#!/usr/bin/env python3

'''
Parse IPDB database files.

Get it here: http://ip.zxinc.org/index.htm

License: GPLv3 or later
'''

import os
from struct import unpack
import mmap
import ipaddress
from typing import Tuple, List
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

class DatabaseError(Exception): pass

class IpInfo(namedtuple('IpInfo', 'start end info')):
  pass

class IPDB:
  def __init__(self, dbfile, charset='utf-8'):
    if isinstance(dbfile, (str, bytes, os.PathLike)):
      dbfile = open(dbfile, 'rb')

    self.charset = charset
    self.f = f = mmap.mmap(dbfile.fileno(), 0, access=mmap.MAP_SHARED)

    magic = f[0:4]
    if magic != b'IPDB':
      raise DatabaseError('bad magic')

    self.index_base_offset = unpack('<Q', f[16:24])[0] #索引区基址

    iplen = f[7]
    if iplen == 4:
      self.ip_version = 4
      self._read_index = self._read_index_v4
      self._int_to_ip = self._int_to_ip_v4
      real_count = (len(f) - self.index_base_offset) // 7
    elif iplen == 8:
      self.ip_version = 6
      self._read_index = self._read_index_v6
      self._int_to_ip = self._int_to_ip_v6
      real_count = (len(f) - self.index_base_offset) // 11
    else:
      raise DatabaseError('unsupported ip length', iplen)

    count = unpack('<Q', f[8:16])[0]
    if real_count != count:
      logger.warning('real count != reported count! %s != %s',
                     real_count, count)
    self.count = real_count
    self.address_segment_len = f[24] if f[4] != 1 else 2

  def lookup(self, ip):
    ip = ipaddress.ip_address(ip)
    if ip.version != self.ip_version:
      raise ValueError('wrong IP address version, supported is %s'
                       % self.ip_version)

    if ip.version == 6:
      needle = int(ip) >> 8 * 8
    else:
      needle = int(ip)

    return self._search_record(needle)

  def _search_record(self, needle: int) -> IpInfo:
    lo = 0
    hi = self.count - 1
    read_index = self._read_index

    if needle < read_index(lo)[0]:
      raise LookupError('IP not found')
    else:
      ip, offset = read_index(hi)
      if needle >= ip:
        info = self._read_rec(offset)
        return IpInfo(self._int_to_ip(ip), None, info)

    loip = 0
    if self.ip_version == 4:
      hiip = 0xffff_ffff
    else:
      hiip = 0xffff_ffff_ffff_ffff

    hit = self.index_base_offset
    while lo + 1 < hi:
      mi = (lo + hi) // 2
      ip, offset = read_index(mi)
      if ip <= needle:
        lo = mi
        loip = ip
        hit = offset
      else:
        hi = mi
        hiip = ip

    info = self._read_rec(hit)
    return IpInfo(self._int_to_ip(loip), self._int_to_ip(hiip), info)

  def _int_to_ip_v4(self, i: int) -> ipaddress.IPv4Address:
    return ipaddress.IPv4Address(i)

  def _int_to_ip_v6(self, i: int) -> ipaddress.IPv6Address:
    return ipaddress.IPv6Address(i << 8 * 8)

  def _read_index_v4(self, i):
    pos = self.index_base_offset + i * 7
    data = self.f[pos:pos+7] + b'\x00'
    ip, offset = unpack('<LL', data)
    return ip, offset

  def _read_index_v6(self, i):
    pos = self.index_base_offset + i * 11
    data = self.f[pos:pos+11] + b'\x00'
    ip, offset = unpack('<QL', data)
    logger.debug('reading index %d at %x, and got IP %s',
                 i, pos, self._int_to_ip(ip))
    return ip, offset

  def _read_rec(self, pos: int) -> List[str]:
    logger.debug('reading record at %x', pos)
    f = self.f
    result = []
    for _ in range(self.address_segment_len):
      typ = f[pos]
      if typ == 2:
        new_pos = _parse_offset(f[pos+1:pos+4])
        s, _ = self._read_cstring(new_pos)
        pos += 4
      else:
        s, pos = self._read_cstring(pos)
      result.append(s)
    return result

  def _read_cstring(self, start: int) -> Tuple[str, int]:
    logger.debug('reading C string at %x', start)
    if start == 0:
      return '(null)', start + 1

    end = self.f.find(b'\x00', start)
    if end < 0:
      raise Exception('fail to read C string')
    data = self.f[start:end]
    return data.decode(self.charset, errors='replace'), end + 1

  def __str__(self):
    return ('%s %d条数据' % (
      ' '.join(self.version_info()),
      self.count,
    ))

  def version_date(self):
    d = ''.join(
      x for x in self.version_info()[-1]
      if x.isdigit()
    )
    return int(d)

  def version_info(self):
    _, pos = self._read_index(self.count - 1)
    return self._read_rec(pos)

def _parse_offset(data: bytes) -> int:
  data = data + b'\x00'
  return unpack('<L', data)[0]

def update(file, q):
  import urllib.request
  import tempfile
  import sys
  import shutil
  import subprocess
  import re

  from myutils import safe_overwrite

  try:
    tmp_dir = tempfile.mkdtemp(prefix='IPDB')
    try:
      D = IPDB(file)
    except OSError as e:
      print('注意：原数据文件无法打开：', e, file=sys.stderr)
      D = None

    req = urllib.request.urlopen('http://ip.zxinc.org/index.htm')
    page = req.read().decode('utf-8')
    date = re.findall(r'版本(\d{8})', page)[0]
    date = int(date)

    if D and date <= D.version_date():
      if not q:
        print(D, '是最新的！', file=sys.stderr)
      return
    else:
      if q != 2:
        print(D and D.version_info()[1] or '', f'{date}版', '开始下载...',
              file=sys.stderr, flush=True)

    wget = ['wget']
    if q:
      wget.append('-q')
    subprocess.run(['wget', 'http://ip.zxinc.org/ip.7z'], check=True,
                   cwd=tmp_dir)
    subprocess.run(['7z', 'x', 'ip.7z'], check=True, cwd=tmp_dir)

    with open(os.path.join(tmp_dir, 'ipv6wry.db'), 'rb') as f:
      d = f.read()

    safe_overwrite(file, d, mode='wb')
    old_c = D and D.count or 0
    D = IPDB(file)
    if q != 2:
      print('已经更新！数据条数 %d->%d.' % (old_c, D.count),
            file=sys.stderr)
  finally:
    shutil.rmtree(tmp_dir)

def main():
  DEFAULT_FILE_LOCATION = os.path.expanduser('~/etc/data/ipv6wry.db')
  import argparse
  parser = argparse.ArgumentParser(description='zxinc IP数据库查询与更新')
  parser.add_argument('IP', nargs='*',
                      help='要查询的IP')
  parser.add_argument('-f', '--file',
                      default=DEFAULT_FILE_LOCATION,
                      help='数据库文件路径')
  parser.add_argument('-u', '--update', action='store_true', default=False,
                      help='更新数据库')
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
    update(args.file, q)
    return

  D = IPDB(args.file)

  ips = args.IP
  if not ips:
    print(D)
  elif len(ips) == 1:
    print(' '.join(D.lookup(ips[0]).info))
  else:
    for ip in ips:
      print(D.lookup(ip))

if __name__ == '__main__':
  main()
