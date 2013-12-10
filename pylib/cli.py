# vim:fileencoding=utf-8
# This file is in the Public Domain

'''
Convenient functions for command-line use.

Python 2 & 3
'''

import os

def repl(local, histfile=None, banner=None):
  import readline
  import rlcompleter
  readline.parse_and_bind('tab: complete')
  if histfile is not None and os.path.exists(histfile):
    # avoid duplicate reading
    readline.clear_history()
    readline.set_history_length(10000)
    readline.read_history_file(histfile)
  import code
  readline.set_completer(rlcompleter.Completer(local).complete)
  code.interact(local=local, banner=banner)
  if histfile is not None:
    readline.write_history_file(histfile)

def repl_reset_stdin(*args, **kwargs):
  fd = os.open('/dev/tty', os.O_RDONLY)
  os.dup2(fd, 0)
  os.close(fd)
  repl(*args, **kwargs)

def repl_py27(local, *args, **kwargs):
  '''Fix unicode display in Python 2.x by filtering through the ascii2uni program'''
  import subprocess, sys, time
  p = subprocess.Popen(['ascii2uni', '-qa7'],
                       stdin=subprocess.PIPE, preexec_fn=os.setpgrp)

  def displayfunc(value):
    if value is None:
      local['_'] = None
      return

    value = repr(value)
    if value.find(r'\x') != -1:
      p.stdin.write(value+'\n')
      time.sleep(0.01)
    else:
      print(value)
    local['_'] = value

  sys.displayhook = displayfunc
  try:
    repl(local, *args, **kwargs)
  finally:
    p.stdin.close()
    p.wait()
