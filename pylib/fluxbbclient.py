# vim:fileencoding=utf-8

import urllib.parse

from lxml.html import fromstring

import httpsession

class FluxBB(httpsession.Session):
  def __init__(self, urlprefix, *args, **kwargs):
    self.urlprefix = urlprefix
    super().__init__(*args, **kwargs)

  def check_login(self):
    '''check if we have logged in already (by cookies)'''
    res = self.bbsrequest('/')
    body = res.read().decode('utf-8')
    return len(fromstring(body).xpath('//div[@id="brdwelcome"]/*[@class="conl"]/li')) > 0

  def login(self, username, password):
    post = {
      'req_username': username,
      'req_password': password,
      'save_pass': '1',
      'form_sent': '1',
    }
    res = self.bbsrequest('/login.php?action=in', post)
    body = res.read()
    if body.find(b'http-equiv="refresh"') == -1:
      return False
    else:
      return True

  def delete_unverified_users(self, doc=None):
    '''delete inverified users in first page
    
    doc can be given if you have that page's parsed content alread.
    return False if no such users are found.
    '''
    if doc is None:
      res = self.bbsrequest('/admin_users.php?find_user=&order_by=username&direction=ASC&user_group=0&p=1')
      body = res.read().decode('utf-8')
      doc = fromstring(body)
    trs = doc.xpath('//div[@id="users2"]//tbody/tr')
    if not trs:
      return False

    users = [tr.xpath('td/input[@type="checkbox"]/@name')[0][6:-1] for tr in trs]
    users = ','.join(users)

    post = {
      'ban_expire': '',
      'ban_users_comply': 'save',
      'ban_message': 'spam',
      'ban_the_ip': '1',
      'users': users,
    }
    res = self.bbsrequest('/admin_users.php', post, headers={
      'Referer': urllib.parse.urljoin(self.urlprefix, '/admin_users.php'),
    })
    body = res.read().decode('utf-8')

    post = {
      'delete_users_comply': 'delete',
      'delete_posts': '1',
      'users': users,
    }
    res = self.bbsrequest('/admin_users.php', post, headers={
      'Referer': urllib.parse.urljoin(self.urlprefix, '/admin_users.php'),
    })
    body = res.read().decode('utf-8')
    return True

  def bbsrequest(self, path, *args, **kwargs):
    url = urllib.parse.urljoin(self.urlprefix, path)
    return self.request(url, *args, **kwargs)
