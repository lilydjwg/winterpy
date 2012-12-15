import os
from collections import defaultdict, namedtuple

from pkg_resources import parse_version

class PkgNameInfo(namedtuple('PkgNameInfo', 'name, version, release, arch')):
  def __lt__(self, other):
    if self.name != other.name or self.arch != other.arch:
      return NotImplemented
    if self.version != other.version:
      return parse_version(self.version) < parse_version(other.version)
    return int(self.release) < int(other.release)

  def __gt__(self, other):
    # No, try the other side please.
    return NotImplemented

  @property
  def fullversion(self):
    return '%s-%s' % (self.version, self.release)

  @classmethod
  def parseFilename(cls, filename):
    return cls(*trimext(filename, 3).rsplit('-', 3))

def trimext(name, num=1):
  for i in range(num):
    name = os.path.splitext(name)[0]
  return name

def finddups(pkgs, n=1):
  ret = defaultdict(list)
  for f in pkgs:
    name, ver, build, arch = PkgNameInfo.parseFilename(os.path.split(f)[1])
    ret[name].append('%s-%s' % (ver, build))
  return {k: sorted(v) for k, v in ret.items() if len(v) > n}
