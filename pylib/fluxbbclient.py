from requestsutils import RequestsBase
from htmlutils import parse_document_from_requests, html
from dataclasses import dataclass

@dataclass
class NewPostInfo:
  title: str
  author: str
  link: str
  subforum: str

class FluxBB(RequestsBase):
  userAgent = 'A Python Fluxbb Client by lilydjwg'
  auto_referer = True

  def check_login(self):
    '''check if we have logged in already (by cookies)'''
    res = self.request('/')
    doc = parse_document_from_requests(res)
    return len(doc.xpath(
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

    doc can be given if you have that page's parsed content already.
    return False if no such users are found.
    '''
    if doc is None:
      url = '/admin_users.php?find_user=&' \
          'order_by=username&direction=ASC&user_group=0&p=1'
      if since:
        url += '&registered_before=' + since.strftime('%Y-%m-%d %H:%M:%s')
      res = self.request(url)
      doc = parse_document_from_requests(res)
    trs = doc.xpath('//div[@id="users2"]//tbody/tr')
    if not trs:
      return False

    users = [tr.xpath('td/input[@type="checkbox"]/@name')[0][6:-1]
             for tr in trs]
    users = ','.join(users)

    post = {
      'delete_users_comply': 'delete',
      'delete_posts': '1',
      'users': users,
    }
    res = self.request('/admin_users.php', data=post)
    res.text
    return True

  def edit_post(self, post_id, body, *, subject=None, sticky=False):
    r = self.request('/viewtopic.php?pid=%s' % post_id)
    post = parse_document_from_requests(r)
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

  def delete_post(self, post_id):
    self.request('/delete.php?id=%d' % post_id).content
    data = {
      'delete': '删除',
    }
    self.request('/delete.php?id=%d' % post_id, data=data).content

  def block_user(self, user_id):
    r = self.request('/profile.php?section=admin&id=%d' % user_id)
    r.content

    data = {
      'form_sent': '1',
      'group_id': '4',
      'ban': '阻止用户',
    }
    r = self.request('/profile.php?section=admin&id=%d' % user_id, data=data)
    doc = parse_document_from_requests(r)
    r = self.request('/admin_bans.php?add_ban=%d' % user_id)
    doc = parse_document_from_requests(r)
    form = doc.forms[0]
    form.fields['ban_message'] = 'spam'
    r = self.request(form.action, data=dict(form.fields))
    r.content

  def get_post_ids_from_topic(self, topic_id):
    r = self.request('/viewtopic.php?id=%d' % topic_id)
    doc = parse_document_from_requests(r)
    links = doc.xpath('//div[@id]/h2//a')
    pids = [int(x.get('href').split('#', 1)[-1][1:])
            for x in links]
    return pids

  def get_user_topic_ids(self, user_id):
    r = self.request('/search.php?action=show_user_topics&user_id=%d' % user_id)
    doc = parse_document_from_requests(r)
    links = doc.xpath('//td[@class="tcl"]/div[@class="tclcon"]/div//a')
    tids = [int(x.get('href').split('=', 1)[-1])
            for x in links
            if x.getparent().tag != 'span'
           ]
    return tids

  def get_new_posts(self) -> tuple[list[NewPostInfo], html.HtmlElement]:
    r = self.request('/search.php?action=show_new')
    if r.status_code == 403:
      raise PermissionError

    doc = parse_document_from_requests(r)
    rows = doc.xpath('//div[@id="vf"]//tr[contains(@class, "inew")]')

    new_posts = []
    for row in rows:
      a = row.xpath('./td//a')[0]
      title = a.text
      link = a.get('href')
      author = a.getnext().text.removeprefix('by ')
      subforum = row.xpath('./td[2]//a')[0].text
      new_posts.append(NewPostInfo(title, author, link, subforum))

    return new_posts, doc

  def mark_all_as_read(self, doc: html.HtmlElement) -> None:
    a = doc.xpath('//p[@class="subscribelink clearb"]/a')[0]
    self.request(a.get('href'))
