import os
from collections import defaultdict, namedtuple
import subprocess
import re

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

def get_pkgname_with_bash(PKGBUILD):
  script = '''\
. '%s'
echo ${pkgname[*]}''' % PKGBUILD
  # Python 3.4 has 'input' arg for check_output
  p = subprocess.Popen(['bash'], stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE)
  output = p.communicate(script.encode('latin1'))[0].decode('latin1')
  ret = p.wait()
  if ret != 0:
    raise subprocess.CalledProcessError(
      ret, ['bash'], output)
  return output.split()

def _run_bash(script):
  p = subprocess.Popen(['bash'], stdin=subprocess.PIPE)
  p.communicate(script.encode('latin1'))
  ret = p.wait()
  if ret != 0:
    raise subprocess.CalledProcessError(
      ret, ['bash'])

def get_aur_pkgbuild_with_bash(name):
  script = '''\
. /usr/lib/yaourt/util.sh
. /usr/lib/yaourt/aur.sh
init_color
aur_get_pkgbuild '%s' ''' % name
  _run_bash(script)

def get_abs_pkgbuild_with_bash(name):
  script = '''\
. /usr/lib/yaourt/util.sh
. /usr/lib/yaourt/abs.sh
init_paths
init_color
arg=$(pacman -Sp --print-format '%%r/%%n' '%s')
RSYNCOPT="$RSYNCOPT -O"
abs_get_pkgbuild "$arg" ''' % name
  _run_bash(script)

pkgfile_pat = re.compile(r'(?:^|/).+-[^-]+-\d+-(?:\w+)\.pkg\.tar\.xz$')

def _strip_ver(s):
  return re.sub(r'[<>=].*', '', s)

def get_package_dependencies(name):
  out = subprocess.check_output(["package-query", "-Sii", "-f", "%D", name])
  out = out.decode('latin1')
  return [_strip_ver(x) for x in out.split() if x != '-']

def get_package_info(name, local=False):
  old_lang = os.environ['LANG']
  os.environ['LANG'] = 'C'
  args = '-Qi' if local else '-Si'
  try:
    out = subprocess.check_output(["pacman", args, name])
    out = out.decode('latin1')
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

def get_package_repository(name):
  try:
    out = subprocess.check_output(["package-query", "-Sii", "-f", "%r", name])
    repo = out.strip().decode('latin1')
  except subprocess.CalledProcessError:
    repo = 'local'
  return repo

def is_official(name):
  repo = get_package_repository(name)
  return repo in ('core', 'extra', 'community', 'multilib', 'testing')
