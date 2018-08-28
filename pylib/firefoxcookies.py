import sqlite3
import encodings.idna
from urllib.parse import urlsplit
import os, tempfile, shutil

import tldextract

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

  def __init__(self, cookiefile):
    with open(cookiefile, 'rb') as db, \
        tempfile.NamedTemporaryFile(delete=False, prefix='fxcookie-') as tmp:
      shutil.copyfileobj(db, tmp)
      tmp.flush()

    self._file_to_delete = tmp.name
    self._db = sqlite3.connect(tmp.name)
    # self._db = sqlite3.connect(cookiefile)
    self._extract = tldextract.TLDExtract(include_psl_private_domains=True)
    try:
      self._db.execute("select 1 from moz_cookies where originAttributes = '' limit 1").fetchall()
      self._origin = True
    except sqlite3.OperationalError:
      self._origin = False

  def get_cookies(self, url):
    """
    Return a list of cookies to be returned to server.

    Ref: https://dxr.mozilla.org/mozilla-central/source/netwerk/cookie/nsCookieService.cpp#3081
    """
    us = urlsplit(url)
    base_domain = self._extract(us.hostname).registered_domain
    base_domain = domain_to_ascii(base_domain)

    sql = '''select name, value, host, path from moz_cookies
             where baseDomain = ?'''
    if us.scheme != 'https':
      sql += ' and isSecure != 1'''
    if self._origin:
      sql += " and originAttributes = ''"

    cursor = self._db.execute(sql, (base_domain,))
    candidates = cursor.fetchall()

    path = us.path or '/'
    domain = domain_to_ascii(us.hostname)
    candidates = [x for x in candidates if domain.endswith(x[2])]
    candidates = [x for x in candidates if path_matches(x[3], path)]

    return {x[0]: x[1] for x in candidates}

