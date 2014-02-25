from lxml.html import fromstring

from requestsutils import RequestsBase

class FluxBB(RequestsBase):
  userAgent = 'A Python Fluxbb Client by lilydjwg'
  auto_referer = True

  def check_login(self):
    '''check if we have logged in already (by cookies)'''
    res = self.request('/')
    body = res.text
    return len(fromstring(body).xpath(
      '//div[@id="brdwelcome"]/*[@class="conl"]/li')) > 0

  def login(self, username, password):
    post = {
      'req_username': username,
      'req_password': password,
      'save_pass': '1',
      'form_sent': '1',
    }
    body = self.request('/login.php?action=in', data=post).content
    return b'http-equiv="refresh"' in body

  def delete_unverified_users(self, doc=None, *, msg=None, since=None):
    '''delete inverified users in first page

    doc can be given if you have that page's parsed content alread.
    return False if no such users are found.
    '''
    if doc is None:
      url = '/admin_users.php?find_user=&' \
          'order_by=username&direction=ASC&user_group=0&p=1'
      if since:
        url += '&registered_before=' + since.strftime('%Y-%m-%d %H:%M:%s')
      res = self.request(url)
      body = res.text
      doc = fromstring(body)
    trs = doc.xpath('//div[@id="users2"]//tbody/tr')
    if not trs:
      return False

    users = [tr.xpath('td/input[@type="checkbox"]/@name')[0][6:-1]
             for tr in trs]
    users = ','.join(users)

    post = {
      'ban_expire': '',
      'ban_users_comply': 'save',
      'ban_message': msg or 'not verified. Ask admin if you are not a spammer.',
      'ban_the_ip': '1',
      'users': users,
    }
    res = self.request('/admin_users.php', data=post)
    body = res.text

    post = {
      'delete_users_comply': 'delete',
      'delete_posts': '1',
      'users': users,
    }
    res = self.request('/admin_users.php', data=post)
    body = res.text
    return True

  def edit_post(self, post_id, body, *, subject=None, sticky=False):
    html = self.request('/viewtopic.php?pid=%s' % post_id).text
    post = fromstring(html)
    old_subject = post.xpath('//ul[@class="crumbs"]/li/strong/a')[0].text
    data = {
      'form_sent': '1',
      'req_message': body,
      'req_subject': subject or old_subject,
      'stick_topic': sticky and '1' or '0',
    }
    url = '/edit.php?id=%s&action=edit' % post_id
    res = self.request(url, data=data)
    return b'http-equiv="refresh"' in res.content

