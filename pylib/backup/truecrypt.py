'''
  Truecrypt mount/unmount
  ~~~~~~~~~~~~~~~~~~~~~~~

  You can store backup files into truecrypt volume.
'''

import logging

from . import base

__all__ = ['mount', 'unmount']

logger = logging.getLogger(__name__)

def mount(source, dest, sudo=False):
  cmd = [
    'truecrypt',
    source,
    dest
  ]
  if sudo:
    cmd.insert(0, 'sudo')
  retcode = base.run_command(cmd)
  if retcode == 0:
    logging.info('mount %s at %s successfully', source, base.bold(dest))
  else:
    logging.error('mounting %s at %s failed with code %d',
                  source,
                  base.bold(dest),
                  retcode)
  return not retcode

def unmount(sudo=False):
  cmd = [
    'truecrypt',
    '-d'
  ]
  if sudo:
    cmd.insert(0, 'sudo')
  retcode = base.run_command(cmd)
  if retcode == 0:
    logging.info('unmount truecrypt volume successfully.')
  else:
    logging.error('unmounting truecrypt volume failed with code %d', retcode)

  return not retcode
