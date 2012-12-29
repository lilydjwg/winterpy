import re
from urllib.parse import urlencode
from getpass import getpass
from collections import defaultdict

from lxml.html import fromstring

from httpsession import Session

idAndTypeParser = re.compile(r"inputUseable\(this, '(?P<hostid>\d+)','(?P<type>\w+)'\)")
authCookiePageURL = re.compile(r'(?<=src=")[^"]+(?=")')

def encodeHost(func):
  def wrapper(self, record):
    record = record.copy()
    record['host'] = urlencode(record['host'])
    func(record)
  return func

class WingDNSError(Exception): pass

class WingDNS(Session):
  UserAgent = 'IP updater'
  def login(self, username, password):
    self.request('http://www.wingdns.com/').read()
    form = {}
    form['username'] = username
    form['pwd'] = password
    form['checkbox'] = 'checkbox'
    r = self.request('http://www.wingdns.com/login.php?step=2', form).read().decode('gb18030')
    for u in authCookiePageURL.findall(r):
      self.request(u).read()

  def getAdminConsole(self, id):
    res = self.request('http://www.wingdns.com/records.php?id=%s' % id).read().decode('cp936')
    if res.startswith('0|'):
      raise WingDNSError(res.split('|', 1)[-1])
    doc = fromstring(res)
    zone = doc.cssselect('#domain_name')[0].text
    self.records = defaultdict(list)
    self.records['zone'] = zone
    for i in doc.cssselect('[value=修改]'):
      m = idAndTypeParser.match(i.get('onclick'))
      if m:
        type = m.group('type')
        r = {}
        r['hostid'] = m.group('hostid')
        tr = i.getparent().getparent()
        r['host'] = tr.cssselect('#sub_domain')[0].value
        r['data'] = tr.cssselect('#value')[0].value
        r['mx'] = tr.cssselect('#mx')[0].value
        self.records[type].append(r)

  @encodeHost
  def add(self, record):
    url = 'http://www.wingdns.com/ajax_records.php?action=add&zone={zone}&num={type}&host={host}&type=0&data={data}&ttl=60&mx={mx}'.format(zone=self.records['zone'], **record)
    r = self.request(url)
    status, hostid = r.read().decode().split('|', 1)
    if status == '1':
      return hostid
    else:
      raise ValueError(hostid)

  @encodeHost
  def modi(self, record):
    url = 'http://www.wingdns.com/ajax_records.php?action=modi&zone={zone}&hostid={hostid}&host={host}&type=0&data={data}&ttl=60&mx={mx}'.format(zone=self.records['zone'], **record)
    r = self.request(url)
    status = r.read().decode().split('|', 1)[0]
    if status != '1':
      raise ValueError(hostid)

  @encodeHost
  def del_(self, record):
    url = 'http://www.wingdns.com/ajax_records.php?action=del&hostid={hostid}&zone={zone}'.format(zone=self.records['zone'], **record)
    r = self.request(url)
    status = r.read().decode().split('|', 1)[0]
    if status != '1':
      raise ValueError(hostid)

  def http_open(self, method, url, values):
    if method == 'GET':
      if '?' in url:
          url += '&'
      else:
          url += '?'
      url += urlencode(values)
      data = None
    else:
      data = urlencode(values)
    return self.request(url, data)

