import os
import sys
import re
import datetime
import stat
import mimetypes
import threading
import email.utils
import time
import logging
import http.client
import traceback
from functools import partial

from tornado.web import HTTPError, RequestHandler, asynchronous, GZipContentEncoding
import tornado.escape

logger = logging.getLogger(__name__)
_legal_range = re.compile(r'bytes=(\d*)-(\d*)$')

class ErrorHandlerMixin:
  '''nicer error page'''
  error_page = '''\
<!DOCTYPE html>
<meta charset="utf-8" />
<title>%(code)s %(message)s</title>
<style type="text/css">
  body { font-family: serif; }
</style>
<h1>%(code)s %(message)s</h1>
<p>%(err)s</p>
<hr/>
'''

  def write_error(self, status_code, **kwargs):
    if self.settings.get("debug") and "exc_info" in kwargs:
      # in debug mode, try to send a traceback
      self.set_header('Content-Type', 'text/plain')
      for line in traceback.format_exception(*kwargs["exc_info"]):
        self.write(line)
      self.finish()
    else:
      err_msg = kwargs.get('exc_info', '  ')[1].log_message
      if err_msg is None:
        err_msg = ''
      else:
        err_msg += '.'

      self.finish(self.error_page % {
        "code": status_code,
        "message": http.client.responses[status_code],
        "err": err_msg,
      })

class FileEntry:
  '''For ``StaticFileHandler`` with directory index enabled'''
  isdir = False
  def __init__(self, path, file):
    st = os.stat(os.path.join(path, file))
    self.time = datetime.datetime.fromtimestamp(st[stat.ST_MTIME])
    self.name = file
    self.filename = file
    if stat.S_ISDIR(st[stat.ST_MODE]):
      self.isdir = True
      self.filename += '/'
    self.size = st[stat.ST_SIZE]

  def __lt__(self, another):
    if self.isdir and not another.isdir:
      return True
    if not self.isdir and another.isdir:
      return False
    return self.name < another.name

class StaticFileHandler(RequestHandler):
  """A simple handler that can serve static content from a directory.

  To map a path to this handler for a static data directory /var/www,
  you would add a line to your application like::

    application = web.Application([
      (r"/static/(.*)", web.StaticFileHandler, {
        "path": "/var/www",
        "default_filenames": ["index.html"], #optional
        "dirindex": "dirlisting", #optional template name for directory listing
      }),
    ])

  The local root directory of the content should be passed as the "path"
  argument to the handler.

  The `dirindex` template will receive the following parameters:
    - `url`: the requested path
    - `files`, a list of ``FileEntry``; override ``FileEntry`` attribute to
      customize (it must be comparable)
    - `decodeURIComponent`, a decoding function

  To support aggressive browser caching, if the argument "v" is given
  with the path, we set an infinite HTTP expiration header. So, if you
  want browsers to cache a file indefinitely, send them to, e.g.,
  /static/images/myimage.png?v=xxx. Override ``get_cache_time`` method for
  more fine-grained cache control.
  """
  CACHE_MAX_AGE = 86400*365*10 #10 years
  BLOCK_SIZE = 40960 # 4096 is too slow; this value works great here
  FileEntry = FileEntry

  _static_hashes = {}
  _lock = threading.Lock()  # protects _static_hashes

  def initialize(self, path, default_filenames=None, dirindex=None):
    self.root = os.path.abspath(path) + os.path.sep
    self.default_filenames = default_filenames
    self.dirindex = dirindex

  @classmethod
  def reset(cls):
    with cls._lock:
      cls._static_hashes = {}

  def head(self, path):
    self.get(path, include_body=False)

  def get(self, path, include_body=True):
    if os.path.sep != "/":
      path = path.replace("/", os.path.sep)
    abspath = os.path.abspath(os.path.join(self.root, path))
    # os.path.abspath strips a trailing /
    # it needs to be temporarily added back for requests to root/
    if not (abspath + os.path.sep).startswith(self.root):
      raise HTTPError(403, "%s is not in root static directory", path)
    self.send_file(path, abspath, include_body)

  def send_file(self, path, abspath, include_body=True):
    '''send a static file to client'''
    # we've found the file
    found = False
    # use @asynchronous on a seperate method so that HTTPError won't get
    # messed up
    if os.path.isdir(abspath):
      # need to look at the request.path here for when path is empty
      # but there is some prefix to the path that was already
      # trimmed by the routing
      if not self.request.path.endswith("/"):
        self.redirect(self.request.path + "/", permanent=True)
        return

      if self.default_filenames is not None:
        for i in self.default_filenames:
          abspath_ = os.path.join(abspath, i)
          if os.path.exists(abspath_):
            abspath = abspath_
            found = True
            break

      if not found:
        if self.dirindex is not None:
          if not include_body:
            raise HTTPError(405)
          self.renderIndex(abspath)
          return
        else:
          raise HTTPError(403, "Directory Listing Not Allowed")

    if (not found and path.endswith('/')) or not os.path.exists(abspath):
      raise HTTPError(404)
    if not os.path.isfile(abspath):
      raise HTTPError(403, "%s is not a file", path)

    self._send_file_async(path, abspath, include_body)

  @asynchronous
  def _send_file_async(self, path, abspath, include_body=True):
    stat_result = os.stat(abspath)
    modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])
    self.set_header("Last-Modified", modified)
    set_length = True

    mime_type, encoding = mimetypes.guess_type(abspath)
    if not mime_type:
      # default is plain text
      mime_type = 'text/plain'
    self.set_header("Content-Type", mime_type)

    # make use of gzip when possible
    if self.settings.get("gzip") and \
        mime_type in GZipContentEncoding.CONTENT_TYPES:
      set_length = False

    file_length = stat_result[stat.ST_SIZE]
    if set_length:
      self.set_header("Content-Length", file_length)
      self.set_header('Accept-Ranges', 'bytes')

    cache_time = self.get_cache_time(path, modified, mime_type)

    if cache_time > 0:
      self.set_header("Expires", datetime.datetime.utcnow() + \
                     datetime.timedelta(seconds=cache_time))
      self.set_header("Cache-Control", "max-age=" + str(cache_time))
    else:
      self.set_header("Cache-Control", "public")

    self.set_extra_headers(path)

    # Check the If-Modified-Since, and don't send the result if the
    # content has not been modified
    ims_value = self.request.headers.get("If-Modified-Since")
    if ims_value is not None:
      date_tuple = email.utils.parsedate(ims_value)
      if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
      if if_since >= modified:
        self.set_status(304)
        self.finish()
        return

    # Check for range requests
    ranges = None
    if set_length:
      ranges = self.request.headers.get("Range")
      if ranges:
        range_match = _legal_range.match(ranges)
        if range_match:
          start = range_match.group(1)
          start = start and int(start) or 0
          stop = range_match.group(2)
          stop = stop and int(stop) or file_length-1
          if start >= file_length:
            raise HTTPError(416)
          self.set_status(206)
          self.set_header('Content-Range', '%d-%d/%d' % (
            start, stop, file_length))

    if not include_body:
      self.finish()
      return

    file = open(abspath, "rb")
    if ranges:
      if start:
        file.seek(start, os.SEEK_SET)
      self._write_chunk(file, length=stop-start+1)
    else:
      self._write_chunk(file, length=file_length)
    self.request.connection.stream.set_close_callback(partial(self._close_on_error, file))

  def renderIndex(self, path):
    files = []
    for i in os.listdir(path):
      try:
        info = self.FileEntry(path, i)
        files.append(info)
      except OSError:
        continue

    files.sort()
    self.render(self.dirindex, files=files, url=self.request.path,
               decodeURIComponent=tornado.escape.url_unescape)

  def _write_chunk(self, file, length):
    size = min(length, self.BLOCK_SIZE)
    left = length - size
    chunk = file.read(size)
    self.write(chunk)
    if left != 0:
      cb = partial(self._write_chunk, file, length=left)
    else:
      cb = self.finish
      file.close()
    self.flush(callback=cb)

  def _close_on_error(self, file):
    logger.info('closing %d on connection close.', file.fileno())
    file.close()

  def set_extra_headers(self, path):
    """For subclass to add extra headers to the response"""
    pass

  def get_cache_time(self, path, modified, mime_type):
    """Override to customize cache control behavior.

    Return a positive number of seconds to trigger aggressive caching or 0
    to mark resource as cacheable, only.

    By default returns cache expiry of 10 years for resources requested
    with "v" argument.
    """
    return self.CACHE_MAX_AGE if "v" in self.request.arguments else 0

  @classmethod
  def make_static_url(cls, settings, path):
    """Constructs a versioned url for the given path.

    This method may be overridden in subclasses (but note that it is
    a class method rather than an instance method).

    ``settings`` is the `Application.settings` dictionary.  ``path``
    is the static path being requested.  The url returned should be
    relative to the current host.
    """
    abs_path = os.path.join(settings["static_path"], path)
    with cls._lock:
      hashes = cls._static_hashes
      if abs_path not in hashes:
        try:
          f = open(abs_path, "rb")
          hashes[abs_path] = hashlib.md5(f.read()).hexdigest()
          f.close()
        except Exception:
          logging.error("Could not open static file %r", path)
          hashes[abs_path] = None
      hsh = hashes.get(abs_path)
    static_url_prefix = settings.get('static_url_prefix', '/static/')
    if hsh:
      return static_url_prefix + path + "?v=" + hsh[:5]
    else:
      return static_url_prefix + path

def apache_style_log(handler):
  request = handler.request
  ip = request.remote_ip
  dt = time.strftime('[%d/%b/%Y:%H:%M:%S %z]')
  req = '"%s %s %s"' % (request.method, request.uri, request.version)
  status = handler.get_status()
  if 300 <= status < 400:
    length = '-'
  else:
    length = handler._headers.get('Content-Length', '-')
  referrer = '"%s"' % request.headers.get('Referer', '-')
  ua = '"%s"' % request.headers.get('User-Agent', '-')
  f = handler.application.settings.get('log_file', sys.stderr)
  print(ip, '- -', dt, req, status, length, referrer, ua, file=f)
  f.flush()
