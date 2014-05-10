# vim:fileencoding=utf-8

import re
from email import header
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

addr_re = re.compile(r'(.*?)\s+(<[^>]+>)($|,\s*)')

def decode_multiline_header(s):
  ret = []

  for b, e in header.decode_header(re.sub(r'\n\s+', ' ', s)):
    if e:
      if e.lower() == 'gb2312':
        e = 'gb18030'
      b = b.decode(e)
    elif isinstance(b, bytes):
      b = b.decode('ascii')
    ret.append(b)

  return ''.join(ret)

def assemble_mail(subject, to, from_, html=None, text=None):
  if html is None and text is None:
    raise TypeError('no message given')

  if html:
    html = MIMEText(html, 'html', 'utf-8')
  if text:
    text = MIMEText(text, 'plain', 'utf-8')

  if html and text:
    msg = MIMEMultipart('alternative', _subparts = [text, html])
  else:
    msg = html or text

  msg['Subject'] = encode_header(subject)
  msg['From'] = encode_header_address(from_)
  msg['To'] = encode_header_address(to)

  return msg

def encode_header_address(s):
  return addr_re.sub(_addr_submatch, s)

def encode_header(s):
  return Header(s, 'utf-8').encode() if not eight_bit_clean(s) else s

def _addr_submatch(m):
  return encode_header(m.group(1)) + ' ' + m.group(2) + m.group(3)

def eight_bit_clean(s):
  return all(ord(c) < 128 for c in s)
