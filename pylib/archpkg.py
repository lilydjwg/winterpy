from __future__ import annotations

import os
from collections import namedtuple
import subprocess
import re
from typing import List, Dict

import pyalpm

class PkgNameInfo(namedtuple('PkgNameInfo', 'name, version, release, arch')):
  def __lt__(self, other) -> bool:
    if self.name != other.name or self.arch != other.arch:
      return NotImplemented
    if self.version != other.version:
      return pyalpm.vercmp(self.version, other.version) < 0
    return float(self.release) < float(other.release)

  def __gt__(self, other) -> bool:
    # No, try the other side please.
    return NotImplemented

  @property
  def fullversion(self) -> str:
    return '%s-%s' % (self.version, self.release)

  @classmethod
  def parseFilename(cls, filename: str) -> 'PkgNameInfo':
    return cls(*trimext(filename, 3).rsplit('-', 3))

def trimext(name: str, num: int = 1) -> str:
  for i in range(num):
    name = os.path.splitext(name)[0]
  return name

def get_pkgname_with_bash(PKGBUILD: str) -> List[str]:
  script = '''\
. '%s'
echo ${pkgname[*]}''' % PKGBUILD
  # Python 3.4 has 'input' arg for check_output
  p = subprocess.Popen(
    ['bwrap', '--unshare-all', '--ro-bind', '/', '/', '--tmpfs', '/home',
     '--tmpfs', '/run', '--die-with-parent',
     '--tmpfs', '/tmp', '--proc', '/proc', '--dev', '/dev', '/bin/bash'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
  )
  output = p.communicate(script.encode())[0].decode()
  ret = p.wait()
  if ret != 0:
    raise subprocess.CalledProcessError(
      ret, ['bash'], output)
  return output.split()

pkgfile_pat = re.compile(r'(?:^|/).+-[^-]+-[\d.]+-(?:\w+)\.pkg\.tar\.(?:xz|zst)$')

def _strip_ver(s: str) -> str:
  return re.sub(r'[<>=].*', '', s)

def get_package_info(name: str, local: bool = False) -> Dict[str, str]:
  old_lang = os.environ['LANG']
  os.environ['LANG'] = 'C'
  args = '-Qi' if local else '-Si'
  try:
    outb = subprocess.check_output(["pacman", args, name])
    out = outb.decode('latin1')
  finally:
    os.environ['LANG'] = old_lang

  ret = {}
  for l in out.splitlines():
    if not l:
      continue
    if l[0] not in ' \t':
      key, value = l.split(':', 1)
      key = key.strip()
      value = value.strip()
      ret[key] = value
    else:
      ret[key] += ' ' + l.strip()
  return ret

