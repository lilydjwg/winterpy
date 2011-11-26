import logging

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
