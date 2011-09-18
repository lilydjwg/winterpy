#!/usr/bin/env python3
# vim: set fileencoding=utf-8:
# @Name: truecrypt.py

'''
  Truecrypt mount/unmount
  ~~~~~~~~~~~~~~~~~~~~~~~

  You can store backup files into truecrypt volume.
'''


import logging
from getpass import getpass

from . import base

__all__ = ['mount', 'unmount']

logger = logging.getLogger(__name__)


def mount(source, dest='/opt/backup', password=False, sudo=False):
  cmd = [
    'truecrypt',
    source,
    dest
  ]
  if password:
    ps = getpass('Truecrypt password:\n')
    cmd.extend(['-p', ps])
  if sudo:
    cmd.insert(0, 'sudo')
  retcode = base.run_command(cmd)
  if retcode == 0:
    logging.info('Mount %s at %s successfully', source, base.bold(dest))
  else:
    logging.error('Mount %s at %s is failed with code %d',
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
    logging.info('Unmount truecrypt volume successfully.')
  else:
    logging.error('Unmount truecrypt volume is failed with code %d', retcode)

  return not retcode
