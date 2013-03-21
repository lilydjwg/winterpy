import os
import logging
import subprocess

from . import base

__all__ = ['p7zip', 'tar']

logger = logging.getLogger(__name__)

global_exclude_7z = ['-xr!' + x for x in base.global_exclude]
global_exclude_tar = ['--exclude=' + x for x in base.global_exclude]

def p7zip(name, dstfile, sources, exclude=(), opts=()):
  if isinstance(sources, str):
    sources = [sources]
  cmd = ['7z', 'u', dstfile]
  cmd.extend(global_exclude_7z)
  if exclude:
    exclude = ['-xr!' + x for x in exclude]
    cmd.extend(exclude)
  if opts:
    cmd.extend(opts)
  cmd.extend(sources)

  retcode = base.run_command(cmd)
  if retcode == 0:
    logger.info('7z job %s succeeded', base.bold(name))
  else:
    logger.error('7z job %s failed with code %d',
                 base.bold(name), retcode)
  return not retcode

def tarxz(name, dstfile, sources, sudo=True):
  '''use tar & xz to archive, mainly for system files'''
  if isinstance(sources, str):
    sources = [sources]
  if sudo:
    cmd = ['sudo']
  else:
    cmd = []
  cmd.extend(['tar', 'cvJf', dstfile])
  cmd.extend(global_exclude_tar)
  cmd.extend(sources)

  retcode = base.run_command(cmd)
  if retcode == 0:
    logger.info('tar job %s succeeded', base.bold(name))
  else:
    logger.error('tar job %s failed with code %d',
                 base.bold(name), retcode)
  return not retcode

def tar7z(name, dstfile, sources, password=None):
  '''use tar & 7z to archive, mainly for encrypted config files'''
  if isinstance(sources, str):
    sources = [sources]
  cmd = ['tar', 'cv']
  cmd.extend(global_exclude_tar)
  cmd.extend(sources)

  try:
    os.unlink(dstfile) # or 7z will throw errors
  except FileNotFoundError:
    pass
  tar = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  cmd = ['7z', 'a', dstfile, '-si', '-t7z']
  if password is not None:
    cmd.append('-p' + password)
    cmd.append('-mhe')
  p7z = subprocess.Popen(cmd, stdin=tar.stdout, stdout=subprocess.DEVNULL)
  ret1 = tar.wait()
  ret2 = p7z.wait()

  ok = ret1 == ret2 == 0
  if ok:
    logger.info('tar.7z job %s succeeded', base.bold(name))
  else:
    logger.error('tar.7z job %s failed with codes %s',
                 base.bold(name), (ret1, ret2))
  return ok
