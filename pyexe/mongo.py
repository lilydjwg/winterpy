#!/usr/bin/env python3

import sys
import os
from pprint import pprint
import subprocess
import argparse
import urllib.parse

from pymongo import MongoClient
import pymongo.cursor
from bson import ObjectId
assert ObjectId

from cli import repl
from yamlutils import edit_as_yaml
assert edit_as_yaml

import locale
locale.setlocale(locale.LC_ALL, '')
del locale

env = os.environ.copy()
if env['TERM'].find('256') != -1:
  env['TERM'] = env['TERM'].split('-', 1)[0]

def displayfunc(value):
  if value is None:
    v['_'] = None
    return

  if isinstance(value, pymongo.cursor.Cursor):
    p = subprocess.Popen(['colorless', '-l', 'python'], stdin=subprocess.PIPE,
                        universal_newlines=True, env=env)
    value = list(value)
    pprint(value, stream=p.stdin)
    p.stdin.close()
    p.wait()
  elif isinstance(value, pymongo.results.InsertOneResult):
    print(f'<InsertOneResult: acknowledged: {value.acknowledged}, inserted_id: {value.inserted_id!r}>')
  elif isinstance(value, pymongo.results.InsertManyResult):
    print(f'<InsertManyResult: acknowledged: {value.acknowledged}, inserted_ids: {value.inserted_ids!r}>')
  elif isinstance(value, pymongo.results.DeleteResult):
    print(f'<DeleteResult: acknowledged: {value.acknowledged}, deleted_count: {value.deleted_count}>')
  elif isinstance(value, pymongo.results.UpdateResult):
    print(f'<UpdateResult: acknowledged: {value.acknowledged}, matched_count: {value.matched_count}, modified_count: {value.modified_count}, upserted_id: {value.upserted_id}>')
  else:
    pprint(value)
  v['_'] = value

def find_by_id(collection, id):
  return db[collection].find_one({'_id': ObjectId(id)})

def main(url, kwargs):
  global db, conn
  if not url:
    url = ['mongodb://localhost/']
  conn = MongoClient(host=url, **kwargs)
  try:
    dbname = urllib.parse.urlsplit(url[0]).path.lstrip('/') or 'test'
  except IndexError:
    dbname = 'test'
  db = conn[dbname]

  rc = os.path.expanduser('~/.mongorc.py')
  if os.path.isfile(rc):
    exec(compile(open(rc, 'rb').read(), '.mongorc.py', 'exec'))

  global v
  v = globals().copy()
  v.update(locals())
  v['_'] = None
  del v['repl'], v['kwargs'], v['main']
  del v['displayfunc'], v['subprocess'], v['env']
  del v['__name__'], v['__cached__'], v['__doc__'], v['__file__'], v['__package__']
  del v['rc'], v['argparse']
  sys.displayhook = displayfunc

  repl(
    v, os.path.expanduser('~/.mongo_history'),
    banner = 'Python MongoDB console',
  )

if __name__ == '__main__':
  try:
    import setproctitle
    setproctitle.setproctitle('mongo.py')
    del setproctitle
  except ImportError:
    pass

  parser = argparse.ArgumentParser(description='MongoDB Shell in Python')
  parser.add_argument('--slaveok', action='store_true')
  parser.add_argument('dburl', nargs='*', default=None,
                      help='mongodo:// URL(s) to connect to')
  args = parser.parse_args()

  kwargs = {}
  if args.slaveok:
    kwargs['slave_okay'] = True

  main(args.dburl, kwargs)
