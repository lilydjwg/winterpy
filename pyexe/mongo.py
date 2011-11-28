#!/usr/bin/env python3
# vim:fileencoding=utf-8

import sys
import os
from pymongo import Connection
import pymongo.cursor
from cli import repl
from pprint import pprint
import subprocess

import locale
locale.setlocale(locale.LC_ALL, '')
del locale

host = 'localhost'
port = 27017
db = 'test'

env = os.environ.copy()
if env['TERM'].find('256'):
  env['TERM'] = env['TERM'].split('-', 1)[0]

def displayfunc(value):
  if value is None:
    return

  if isinstance(value, pymongo.cursor.Cursor):
    p = subprocess.Popen(['colorless', '-l', 'python'], stdin=subprocess.PIPE,
                        universal_newlines=True, env=env)
    pprint(list(value), stream=p.stdin)
    p.stdin.close()
    p.wait()
  else:
    pprint(value)

def main():
  global db
  conn = Connection(host=host, port=port)
  db = conn[db]

  v = globals().copy()
  v.update(locals())
  del v['repl'], v['argv'], v['main'], v['v'], v['host'], v['port']
  del v['displayfunc'], v['subprocess'], v['env']
  del v['__name__'], v['__cached__'], v['__doc__'], v['__file__'], v['__package__']
  sys.displayhook = displayfunc

  repl(
    v, os.path.expanduser('~/.mongo_history'),
    banner = 'Python MongoDB console',
  )

if __name__ == '__main__':
  argv = sys.argv
  if len(argv) == 2:
    if '/' in argv[1]:
      host, db = argv[1].split('/', 1)
    if ':' in host:
      host, port = host.split(':', 1)
  elif len(argv) == 1:
    pass
  else:
    sys.exit('argument error')

  main()
