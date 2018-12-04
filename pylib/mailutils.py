# vim:fileencoding=utf-8

import re
import datetime
import codecs
import smtplib
from email import header
import email.header
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import Message
from typing import Union, Iterable, Optional, cast

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

def decode_payload(m, *, binary=False):
  p = m.get_payload()
  enc = m['Content-Transfer-Encoding']
  ctype = m['Content-Type']
  if enc == '8bit':
    return p
  else:
    data = codecs.decode(p.encode(), enc)
    if not binary:
      charset = get_charset_from_ctype(ctype) or 'utf-8'
      data = data.decode(charset)
    return data

def assemble_mail(
  subject: str, to: Union[str, Iterable[str]], from_: str,
  html: Optional[str] = None, text: Optional[str] = None,
):
  if html is None and text is None:
    raise TypeError('no message given')

  html_msg: Optional[MIMEText]
  text_msg: Optional[MIMEText]

  if html:
    html_msg = MIMEText(html, 'html', 'utf-8')
  else:
    html_msg = None

  if text:
    text_msg = MIMEText(text, 'plain', 'utf-8')
  else:
    text_msg = None

  msg: Message
  if html_msg and text_msg:
    msg = MIMEMultipart('alternative', _subparts = [text_msg, html_msg])
  else:
    msg = cast(Message, html_msg or text_msg)

  msg['Subject'] = encode_header(subject)
  msg['From'] = encode_header_address(from_)
  if isinstance(to, str):
    msg['To'] = encode_header_address(to)
  else:
    msg['To'] = ', '.join(encode_header_address(x) for x in to)

  return msg

def encode_header_address(s):
  return addr_re.sub(_addr_submatch, s)

def encode_header(s):
  return Header(s, 'utf-8').encode() if not eight_bit_clean(s) else s

def decode_header(h):
  var = email.header.decode_header(h)[0]
  charset = var[1] or 'ascii'
  if charset.lower() == 'gb2312': #fxxk
    charset = 'gb18030'
  try:
    var = var[0].decode(charset)
  except AttributeError:
    var = var[0]
  except LookupError:
    var = var[0].decode('utf-8', errors='replace')
  return var

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

def save_html_mail(msg):
  import os
  import tempfile

  basedir = tempfile.mkdtemp()

  def save_file(fname, content):
    fname = os.path.join(basedir, fname)
    if isinstance(content, str):
      f = open(fname, 'w')
    else:
      f = open(fname, 'wb')
    f.write(content)

  def name_gen():
    i = 1
    while True:
      yield str(i)
      i += 1
  name_it = name_gen()

  m = msg
  title = decode_header(m['Subject'])
  mailtype = m.get_content_type()
  if mailtype == 'multipart/alternative':
    mainMail = [m for m in m.get_payload()
                if m.get_content_type() == 'text/html'][0]
    mailbody = decode_payload(mainMail)
  elif mailtype in ('multipart/related', 'multipart/mixed'):
    mails = m.get_payload()
    cidMapping = {}
    for mail in mails:
      if mail.get_content_type() == 'multipart/alternative':
        mainMail = [m for m in mail.get_payload()
                    if m.get_content_type() == 'text/html'][0]
        mailbody = decode_payload(mainMail)
      elif mail.get_content_type().startswith('text/html'):
        mailbody = decode_payload(mail)
      else:
        try:
          cid = mail['Content-ID'][1:-1]
        except TypeError:
          if mail['Content-Disposition'] and \
             mail['Content-Disposition'].find('attachment') != -1:
            continue
          raise
        fname = decode_header(mail.get_filename() or next(name_it))
        cidMapping[cid] = fname
        body = decode_payload(mail, binary=True)
        save_file(fname, body)
  elif mailtype == 'text/html':
    mailbody = decode_payload(m)
  else:
    raise NotImplementedError('type %s not recognized' % mailtype)

  from lxml.html import fromstring, tostring # type: ignore
  from lxml.html import builder as E

  div = fromstring(mailbody)
  for cidLink in div.xpath('//*[starts-with(@src, "cid:")]'):
    cid = cidLink.get('src')[4:]
    cidLink.set('src', cidMapping[cid])
  div.insert(0, E.TITLE(title))
  div.insert(0, E.META(charset='utf-8'))
  mailbody_b = tostring(div, encoding='utf-8')
  save_file('index.html', mailbody_b)

  return os.path.join(basedir, 'index.html')

