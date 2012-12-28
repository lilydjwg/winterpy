'''
backups based on git.

We cannot `chdir` to the working directory because we may run multiple backups
at the same time.
'''

import os
import logging

from . import base

__all__ = ['push', 'fetch']

logger = logging.getLogger(__name__)

def push(name, directory, remote='origin', branch=None, *, force=False):
  cmd = [
    'git',
    '--work-tree='+directory,
    '--git-dir='+os.path.join(directory, '.git'),
    'push',
    remote
  ]
  if branch:
    cmd.append(branch)
  if force:
    cmd.append('-f')
  retcode = base.run_command(cmd)
  if retcode == 0:
    logger.info('git job %s succeeded', base.bold(name))
  else:
    logger.error('git job %s failed with code %d', base.bold(name), retcode)
  return not retcode

def fetch(name, directory, srcdir):
  '''
  fetch from the destination

  if the `directory` does not exist, we'll clone it instead.
  '''
  if not os.path.exists(directory):
    cmd = [
      'git', 'clone',
      srcdir, directory,
    ]
    cloning = True
  else:
    cmd = [
      'git',
      '--git-dir='+os.path.join(directory, '.git'),
      '--work-tree='+directory,
      'fetch',
    ]
    cloning = False

  verb = ('cloned', 'clone') if cloning else ('fetched', 'fetch')

  retcode = base.run_command(cmd)
  if retcode == 0:
    logger.info('git job %s %s successfully', base.bold(name), verb[0])
  else:
    logger.error('git job %s failed to %s with code %d',
                 base.bold(name), verb[1], retcode)
  return not retcode

#FIXME git-pull has a problem, see http://stackoverflow.com/questions/5083224/git-pull-while-not-in-a-git-directory
# fallback to fetch
pull = fetch
