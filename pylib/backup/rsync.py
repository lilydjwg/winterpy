#!/usr/bin/env python3
# vim:fileencoding=utf-8

import logging

from . import base

__all__ = ['sync2win', 'sync2native']

logger = logging.getLogger(__name__)

global_exclude = ['--exclude=' + x for x in base.global_exclude]

def sync(name, src, dst, option, really, filelist):
  if filelist:
    cmd = [
      'rsync',
      option,
      '--delete',
      '--delete-excluded',
      '-r', '--files-from='+src,
      dst
    ]
  else:
    cmd = [
      'rsync',
      option,
      '--delete',
      '--delete-excluded',
      src, dst
    ]
  cmd.extend(global_exclude)
  if not really:
    cmd.append('-n')
    dry = '(DRY RUN) '
  else:
    dry = ''

  retcode = base.run_command(cmd)
  if retcode == 0:
    logger.info('rsync job %s %ssucceeded', base.bold(name), dry)
  else:
    logger.error('rsync job %s %sfailed with code %d',
                 base.bold(name), dry, retcode)
  return not retcode

def sync2native(name, src, dst, really=False, filelist=False):
  '''
  sync to Linux native filesystems

  `filelist` indicates `src` is a list of files to sync
  '''
  return sync(name, src, dst, '-aviHK', really, filelist)

def sync2win(name, src, dst, really=False, filelist=False):
  '''
  sync to NTFS/FAT filesystems

  `filelist` indicates `src` is a list of files to sync
  '''
  return sync(name, src, dst, '-virtO', really, filelist)
