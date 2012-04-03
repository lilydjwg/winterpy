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
import tempfile
from functools import partial

from tornado.web import HTTPError, RequestHandler, asynchronous, GZipContentEncoding
import tornado.escape
import tornado.httpserver

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

  def initialize(self, path=None, default_filenames=None, dirindex=None):
    if path is not None:
      self.root = os.path.abspath(path) + os.path.sep
    else:
      self.root = None
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
    self.send_file(abspath, include_body)

  def send_file(self, abspath, include_body=True, path=None, download=False):
    '''
    send a static file to client

    ``abspath``: the absolute path of the file on disk
    ``path``: the path to use as if requested, if given
    ``download``: whether we should try to persuade the client to download the
                  file. This can be either ``True`` or the intended filename

    If you use ``send_file`` directly and want to use another file as default
    index, you should set this parameter.
    '''
    # we've found the file
    found = False
    # use @asynchronous on a seperate method so that HTTPError won't get
    # messed up
    if path is None:
      path = self.request.path
    if os.path.isdir(abspath):
      # need to look at the request.path here for when path is empty
      # but there is some prefix to the path that was already
      # trimmed by the routing
      if not path.endswith("/"):
        redir = path + '/'
        if self.request.query:
          redir += '?' + self.request.query
        self.redirect(redir, permanent=True)
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
      raise HTTPError(403, "%s is not a file" % self.request.path)

    if download is not False:
      if download is True:
        filename = os.path.split(path)[1]
      else:
        filename = download
      self.set_header('Content-Disposition', 'attachment; filename='+filename)

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

class HTTPConnection(tornado.httpserver.HTTPConnection):
  _recv_a_time = 8192
  def _on_headers(self, data):
    try:
      data = data.decode('latin1')
      eol = data.find("\r\n")
      start_line = data[:eol]
      try:
        method, uri, version = start_line.split(" ")
      except ValueError:
        raise tornado.httpserver._BadRequestException("Malformed HTTP request line")
      if not version.startswith("HTTP/"):
        raise tornado.httpserver._BadRequestException("Malformed HTTP version in HTTP Request-Line")
      headers = tornado.httputil.HTTPHeaders.parse(data[eol:])
      self._request = tornado.httpserver.HTTPRequest(
        connection=self, method=method, uri=uri, version=version,
        headers=headers, remote_ip=self.address[0])

      content_length = headers.get("Content-Length")
      if content_length:
        content_length = int(content_length)
        use_tmp_files = self._get_handler_info()
        if not use_tmp_files and content_length > self.stream.max_buffer_size:
          raise _BadRequestException("Content-Length too long")
        if headers.get("Expect") == "100-continue":
          self.stream.write(b"HTTP/1.1 100 (Continue)\r\n\r\n")
        if use_tmp_files:
          logging.debug('using temporary files for uploading')
          self._receive_content(content_length)
        else:
          logging.debug('using memory for uploading')
          self.stream.read_bytes(content_length, self._on_request_body)
        return

      self.request_callback(self._request)
    except tornado.httpserver._BadRequestException as e:
      logging.info("Malformed HTTP request from %s: %s",
             self.address[0], e)
      self.stream.close()
      return

  def _receive_content(self, content_length):
    if self._request.method in ("POST", "PUT"):
      content_type = self._request.headers.get("Content-Type", "")
      if content_type.startswith("multipart/form-data"):
        self._content_length_left = content_length
        fields = content_type.split(";")
        for field in fields:
          k, sep, v = field.strip().partition("=")
          if k == "boundary" and v:
            if v.startswith('"') and v.endswith('"'):
              v = v[1:-1]
            self._boundary = b'--' + v.encode('latin1')
            self._boundary_buffer = b''
            self._boundary_len = len(self._boundary)
            break
        self.stream.read_until(b"\r\n\r\n", self._on_content_headers)
      else:
        self.stream.read_bytes(content_length, self._on_request_body)

  def _on_content_headers(self, data, buf=b''):
    self._content_length_left -= len(data)
    data = self._boundary_buffer + data
    logging.debug('file header is %r', data)
    self._boundary_buffer = buf
    header_data = data[self._boundary_len+2:].decode('utf-8')
    headers = tornado.httputil.HTTPHeaders.parse(header_data)
    disp_header = headers.get("Content-Disposition", "")
    disposition, disp_params = tornado.httputil._parse_header(disp_header)
    if disposition != "form-data":
      logging.warning("Invalid multipart/form-data")
      self._read_content_body(None)
    if not disp_params.get("name"):
      logging.warning("multipart/form-data value missing name")
      self._read_content_body(None)
    name = disp_params["name"]
    if disp_params.get("filename"):
      ctype = headers.get("Content-Type", "application/unknown")
      fd, tmp_filename = tempfile.mkstemp(suffix='.tmp', prefix='tornado')
      self._request.files.setdefault(name, []).append(
        tornado.httputil.HTTPFile(
          filename=disp_params['filename'],
          tmp_filename=tmp_filename,
          content_type=ctype,
        )
      )
      self._read_content_body(os.fdopen(fd, 'wb'))
    else:
      logging.warning("multipart/form-data is not file upload, skipping...")
      self._read_content_body(None)

  def _read_content_body(self, fp):
    self.stream.read_bytes(
      min(self._recv_a_time, self._content_length_left),
      partial(self._read_into, fp)
    )

  def _read_into(self, fp, data):
    self._content_length_left -= len(data)
    buf = self._boundary_buffer + data

    bpos = buf.find(self._boundary)
    if bpos != -1:
      if fp:
        fp.write(buf[:bpos-2])
        fp.close()
      spos = buf.find(b'\r\n\r\n', bpos)
      if spos != -1:
        self._boundary_buffer = buf[bpos:spos+4]
        self._on_content_headers(b'', buf=buf[spos+4:])
      elif self._content_length_left > 0:
        self._boundary_buffer = buf[bpos:]
        self.stream.read_until(b"\r\n\r\n", self._on_content_headers)
      else:
        del self._content_length_left
        del self._boundary_buffer
        del self._boundary_len
        del self._boundary
        self.request_callback(self._request)
        return
    else:
      splitpos = -self._boundary_len-1
      if fp:
        fp.write(buf[:splitpos])
      self._boundary_buffer = buf[splitpos:]
      self._read_content_body(fp)

  def _get_handler_info(self):
    request = self._request
    app = self.request_callback
    handlers = app._get_host_handlers(request)
    handler = None
    for spec in handlers:
      match = spec.regex.match(request.path)
      if match:
        handler = spec.handler_class(app, request, **spec.kwargs)
        if spec.regex.groups:
          # None-safe wrapper around url_unescape to handle
          # unmatched optional groups correctly
          def unquote(s):
            if s is None:
              return s
            return tornado.escape.url_unescape(s, encoding=None)
          # Pass matched groups to the handler.  Since
          # match.groups() includes both named and unnamed groups,
          # we want to use either groups or groupdict but not both.
          # Note that args are passed as bytes so the handler can
          # decide what encoding to use.

          if spec.regex.groupindex:
            kwargs = dict(
              (str(k), unquote(v))
              for (k, v) in match.groupdict().iteritems())
          else:
            args = [unquote(s) for s in match.groups()]
        break
    if handler:
      return getattr(handler, 'use_tmp_files', False)

class HTTPServer(tornado.httpserver.HTTPServer):
  def handle_stream(self, stream, address):
    HTTPConnection(stream, address, self.request_callback,
                   self.no_keep_alive, self.xheaders)
