import logging
import subprocess

logger = logging.getLogger(__name__)

__all__ = ['bold', 'run_command']

global_exclude = [
  '__pycache__', '*.pyc',
  '*.swp', '*~',
]

try:
  import curses
  curses.setupterm()
  _bold = str(curses.tigetstr("bold"), "ascii")
  _reset = str(curses.tigetstr("sgr0"), "ascii")
except:
  logger.warn('curses error, plain text log expected')
  _bold = _reset = ''

def bold(text):
  if _bold:
    return _bold + text + _reset
  else:
    return text

def run_command(cmd):
  logger.debug('running command: %r', cmd)

  if cmd[0] == 'sudo':
    print('sudo password may be request.')

  retcode = subprocess.call(cmd)
  return retcode
