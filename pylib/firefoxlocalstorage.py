import os
import sqlite3
from urllib.parse import urlsplit
import tempfile
import shutil

class FirefoxLocalStorage:
  _file_to_delete = None

  def __init__(self, dbfile, copydb=False):
    if copydb:
      with open(dbfile, 'rb') as db, tempfile.NamedTemporaryFile(delete=False) as tmp:
        shutil.copyfileobj(db, tmp)
        tmp.flush()
        self._file_to_delete = tmp.name
        self._db = sqlite3.connect(tmp.name)
    else:
      self._db = sqlite3.connect(dbfile)

  def __del__(self):
    if self._file_to_delete:
      os.unlink(self._file_to_delete)

  def get_records(self, url, *, container_id=None, key=None):
    us = urlsplit(url)
    if us.port:
      port = us.port
    else:
      if us.scheme == 'http':
        port = 80
      elif us.scheme == 'https':
        port = 443
      else:
        raise ValueError('cannot determine port from url %r' % url)

    okey = f'{us.hostname[::-1]}.:{us.scheme}:{port}'
    if container_id is not None:
      if container_id > 0:
        q = f" and originAttributes like '%^userContextId={container_id}%'"
      else:
        q = " and originAttributes == ''"
    else:
      q = None

    sql = '''select originAttributes, scope, key, value
             from webappsstore2
             where originKey = ?'''
    if q is not None:
      sql += q
    if key is not None:
      sql += ' and key = ?'
      cursor = self._db.execute(sql, (okey, key))
    else:
      cursor = self._db.execute(sql, (okey,))

    results = cursor.fetchall()
    return results

if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='query Firefox localstorage')
  parser.add_argument('--ro', default=False, action='store_true',
                     help='handle readonly db')
  parser.add_argument('-k', '--key',
                     help='localstorage key')
  parser.add_argument('file', metavar='FILE',
                     help='webappsstore.sqlite file')
  parser.add_argument('url', metavar='URL',
                     help='URL to use (path ignored)')
  parser.add_argument('container_id', type=int, nargs='?')

  args = parser.parse_args()

  fls = FirefoxLocalStorage(args.file, args.ro)
  results = fls.get_records(
    args.url, container_id=args.container_id, key=args.key)
  if results:
    print('\n'.join('\t'.join(x) for x in results))
