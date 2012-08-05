import os
from collections import defaultdict

def trimext(name, num=1):
  for i in range(num):
    name = os.path.splitext(name)[0]
  return name

def parsePkgName(pkg):
  return trimext(pkg, 3).rsplit('-', 3)

def finddups(pkgs):
  ret = defaultdict(list)
  for f in pkgs:
    name, ver, build, arch = parsePkgName(os.path.split(f)[1])
    ret[name].append('%s-%s' % (ver, build))
  return {n: sorted(v) for n, v in ret.items() if len(v) != 1}
