import sqlite3
import encodings.idna
from urllib.parse import urlsplit
import os, tempfile, shutil
import glob

import tldextractutils

def path_matches(cookie_path, req_path):
  # https://dxr.mozilla.org/mozilla-central/source/netwerk/cookie/nsCookieService.cpp#3047
  cookie_path = cookie_path.rstrip('/')

  if not req_path.startswith(cookie_path):
    return False

  if len(req_path) > len(cookie_path) and req_path[len(cookie_path)] != '/':
    return False

  return True

def domain_to_ascii(domain):
    domain = encodings.idna.nameprep(domain)
    return b'.'.join(
      encodings.idna.ToASCII(x) for x in domain.split('.')
    ).decode('ascii')

class FirefoxCookies:
  _file_to_delete = None

  def __del__(self):
    if self._file_to_delete:
      os.unlink(self._file_to_delete)
      wal_and_shm = glob.glob(self._file_to_delete + '*')
      for f in wal_and_shm:
        os.unlink(f)

  def __init__(self, cookiefile):
    with open(cookiefile, 'rb') as db, \
        tempfile.NamedTemporaryFile(delete=False, prefix='fxcookie-') as tmp:
      shutil.copyfileobj(db, tmp)
      tmp.flush()

    self._file_to_delete = tmp.name
    self._db = sqlite3.connect(tmp.name)
    # self._db = sqlite3.connect(cookiefile)
    try:
      self._db.execute("select 1 from moz_cookies where originAttributes = '' limit 1").fetchall()
      self._origin = True
    except sqlite3.OperationalError:
      self._origin = False

  def get_cookies(self, url):
    """
    Return a list of cookies to be returned to server.

    Ref: https://searchfox.org/mozilla-central/source/netwerk/cookie/nsCookieService.cpp#2952
    """
    us = urlsplit(url)
    base_domain = tldextractutils.extract(
      us.hostname,
      include_psl_private_domains = True,
    ).registered_domain
    base_domain = domain_to_ascii(base_domain)
    domain = domain_to_ascii(us.hostname)

    sql = '''select name, value, host, path from moz_cookies
             where (host = ? or host like ?)'''
    if us.scheme != 'https':
      sql += ' and isSecure != 1'''
    if self._origin:
      sql += " and originAttributes = ''"

    cursor = self._db.execute(sql, (domain, f'%.{base_domain}'))
    candidates = cursor.fetchall()

    path = us.path or '/'
    candidates = [x for x in candidates if domain == x[2] or (x[2][0] == '.' and domain.endswith(x[2]))]
    candidates = [x for x in candidates if path_matches(x[3], path)]

    return {x[0]: x[1] for x in candidates}

