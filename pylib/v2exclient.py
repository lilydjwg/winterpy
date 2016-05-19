from urllib.parse import urljoin

from requestsutils import RequestsBase
from htmlutils import parse_document_from_requests

class V2EXError(Exception):
  pass

class V2EXFailure(V2EXError):
  def __init__(self, msg, req):
    self.msg = msg
    self.req = req

class NotLoggedIn(V2EXError):
  pass

class MissionNotAvailable(V2EXError):
  pass

class V2EX(RequestsBase):
  auto_referer = True
  userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0'

  index_url = 'https://www.v2ex.com/'
  login_url = 'https://www.v2ex.com/signin'
  daily_url = 'https://www.v2ex.com/mission/daily'

  def get_login_things(self):
    r = self.request(self.login_url)
    doc = parse_document_from_requests(r)
    once = doc.xpath('//input[@name="once"]')[0].get('value')
    form = doc.xpath('//form[@action="/signin"]')[0]
    username_field = form.xpath('//input[@type="text"]')[0].get('name')
    password_field = form.xpath('//input[@type="password"]')[0].get('name')
    return form, username_field, password_field

  def login(self, username, password):
    once, username_field, password_field = self.get_login_things()
    post_data = {
      'next': '/',
      username_field: username,
      password_field: password,
      'once': once_value,
    }
    r = self.request(
      self.login_url, 'POST',
      data = post_data,
    )
    if '/signout?once=' not in r.text:
      raise V2EXFailure('login failed', r)

  def daily_mission(self):
    # may need this or mission will fail
    r = self.request(self.index_url)
    if '/signout?once=' not in r.text:
      raise NotLoggedIn

    r = self.request(self.daily_url)
    if 'href="/signin"' in r.text:
      raise NotLoggedIn

    doc = parse_document_from_requests(r)
    buttons = doc.xpath('//input[@value = "领取 X 铜币"]')
    if not buttons:
      raise MissionNotAvailable

    button = buttons[0]
    url = button.get('onclick').split("'")[1]
    r = self.request(urljoin(self.index_url, url))
    if '已成功领取每日登录奖励' not in r.text:
      raise V2EXFailure('daily mission failed', r)
