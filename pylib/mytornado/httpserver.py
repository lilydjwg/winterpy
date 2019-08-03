import os
import sys
import time
import http.client as httpclient
import traceback
import tempfile
from pathlib import Path
from typing import Optional

from tornado.web import (
  HTTPError, RequestHandler,
  StaticFileHandler,
)
import tornado.web
import tornado.escape
import tornado.httpserver
from tornado.log import gen_log
from tornado.web import stream_request_body

from .util import FileEntry

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
      err_exc = kwargs.get('exc_info', '  ')[1]
      if err_exc in (None, ' '):
        err_msg = ''
      else:
        if isinstance(err_exc, HTTPError):
          if err_exc.log_message is not None:
            err_msg = str(err_exc.log_message) + '.'
          else:
            err_msg = ''
        else:
          err_msg = str(err_exc) + '.'

      self.finish(self.error_page % {
        "code": status_code,
        "message": httpclient.responses[status_code],
        "err": err_msg,
      })

  @classmethod
  def patchHandler(cls, RequestHandler):
    '''patch a RequestHandler without subclassing

    In this way we can change all ``tornado.web.RequestHandler``. Simply
subclassing and replacing won't work due to the Python 2-style ``super()``
call in its ``__init__`` method.
    '''
    RequestHandler.write_error = cls.write_error
    RequestHandler.error_page = cls.error_page

class MyStaticFileHandler(StaticFileHandler):
  def initialize(self, path, dirindex_tpl='dir.html'):
    super().initialize(path=path, default_filename='index.html')
    if dirindex_tpl:
      self.dirindex_tpl = dirindex_tpl
    else:
      self.dirindex_tpl = None

  async def get(self, path, include_body=True):
    if self.dirindex_tpl:
      self.path = self.parse_url_path(path)
      absolute_path = self.get_absolute_path(self.root, self.path)

      root = os.path.abspath(self.root)
      if not root.endswith(os.path.sep):
          root += os.path.sep
      if not (absolute_path + os.path.sep).startswith(root):
        raise HTTPError(403, "%s is not in root static directory", self.path)
      if absolute_path is None:
        return

      p = Path(absolute_path)
      if p.is_dir() and not (p / self.default_filename).exists():
        self.absolute_path = None
        return self.render_index(p)

    await super().get(path, include_body=include_body)

  def compute_etag(self) -> Optional[str]:
    if self.absolute_path is None:
      return
    return super().compute_etag()

  def render_index(self, path):
    files = []
    for i in path.iterdir():
      try:
        info = FileEntry(i)
        files.append(info)
      except OSError:
        continue

    files.sort()
    self.render(self.dirindex_tpl, files=files, url=self.request.path,
                decodeURIComponent=tornado.escape.url_unescape)

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

def _on_content_headers(self, data, buf=b''):
  self._content_length_left -= len(data)
  data = self._boundary_buffer + data
  gen_log.debug('file header is %r', data)
  self._boundary_buffer = buf
  header_data = data[self._boundary_len+2:].decode('utf-8')
  headers = tornado.httputil.HTTPHeaders.parse(header_data)
  disp_header = headers.get("Content-Disposition", "")
  disposition, disp_params = tornado.httputil._parse_header(disp_header)
  if disposition != "form-data":
    gen_log.warning("Invalid multipart/form-data")
    self._read_content_body(None)
  if not disp_params.get("name"):
    gen_log.warning("multipart/form-data value missing name")
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
    self._reading_body_into = os.fdopen(fd, 'wb')
    self._read_content_body(self._reading_body_into)
  else:
    gen_log.warning("multipart/form-data is not file upload, skipping...")
    self._read_content_body(None)

def _read_into(self, fp, data, from_handler = False):
  self._content_length_left -= len(data)
  buf = self._boundary_buffer + data

  bpos = buf.find(self._boundary)
  if bpos != -1:
    if fp:
      fp.write(buf[:bpos-2])
      fp.close()
      self._reading_body_into = None
    spos = buf.find(b'\r\n\r\n', bpos)
    if spos != -1:
      self._boundary_buffer = buf[bpos:spos+4]
      _on_content_headers(self, b'', buf=buf[spos+4:])
    elif self._content_length_left > 0:
      self._boundary_buffer = buf[bpos:]
      if from_handler:
        self._reading_headers = True
      else:
        self.stream.read_until(b"\r\n\r\n", self._on_content_headers)
    else:
      del self._content_length_left
      del self._boundary_buffer
      del self._boundary_len
      del self._boundary
      if not from_handler:
        self.request_callback(self._request)
      return
  else:
    splitpos = -self._boundary_len-1
    if fp:
      fp.write(buf[:splitpos])
    self._boundary_buffer = buf[splitpos:]
    if not from_handler:
      # or we'll recurse too deep
      self._read_content_body(fp)

@stream_request_body
class TmpFilesHandler(RequestHandler):
  _boundary = None
  _buffer = b''
  _reading_body_into = None
  _reading_headers = False

  def data_received(self, chunk):
    self._buffer += chunk

    if self._boundary is None and self.request.method in ("POST", "PUT"):
      self._request = self.request
      content_type = self.request.headers.get('Content-Type', '')
      if content_type.startswith('multipart/form-data'):
        self._content_length_left = int(
          self.request.headers.get('Content-Length'))
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

    if self._boundary:
      if self._reading_headers:
        pos = self._buffer.find(b'\r\n\r\n')
        if pos != -1:
          self._reading_headers = False
          _on_content_headers(self, self._buffer[:pos])
          self._buffer = self._buffer[pos:]
      else:
        self._read_content_body(self._reading_body_into)

    if self._buffer:
      self.data_received(b'')

  def _read_content_body(self, fp):
    data = self._buffer
    self._buffer = b''
    _read_into(self, fp, data, from_handler = True)

