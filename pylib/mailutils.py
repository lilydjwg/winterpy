# vim:fileencoding=utf-8

import re
import datetime
import codecs
import smtplib
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

def get_datetime(m):
  d = m['Date']
  # Wed, 18 Jun 2014 04:09:18 +0000
  t = datetime.datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %z')
  # convert to local time
  return datetime.datetime.fromtimestamp(t.timestamp())

def decode_payload(m):
  p = m.get_payload()
  enc = m['Content-Transfer-Encoding']
  ctype = m['Content-Type']
  charset = get_charset_from_ctype(ctype) or 'utf-8'
  if enc == '8bit':
    return p
  else:
    return codecs.decode(p.encode(), enc).decode(charset)

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
  if isinstance(to, (list, tuple, set, frozenset)):
    msg['To'] = ', '.join(encode_header_address(x) for x in to)
  else:
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

def get_charset_from_ctype(ctype):
  pos = ctype.find('charset=')
  if pos > 0:
    charset = ctype[pos+8:]
    if charset.lower() == 'gb2312':
      # Windows misleadingly uses gb2312 when it's gbk or gb18030
      charset = 'gb18030'
    elif charset.lower() == 'windows-31j':
      # cp932's IANA name (Windows-31J), extended shift_jis
      # https://en.wikipedia.org/wiki/Code_page_932
      charset = 'cp932'
    return charset

def sendmail(mail):
  s = smtplib.SMTP()
  s.connect()
  s.send_message(mail)
  s.quit()
