from urllib.parse import urljoin

from requestsutils import RequestsBase
from htmlutils import parse_document_from_requests

class V2EXFailure(Exception):
  def __init__(self, msg, req):
    self.msg = msg
    self.req = req

class V2EX(RequestsBase):
  auto_referer = True
  userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0'

  index_url = 'https://www.v2ex.com/'
  login_url = 'https://www.v2ex.com/signin'
  daily_url = 'https://www.v2ex.com/mission/daily'

  def get_once_value(self):
    r = self.request(self.login_url)
    doc = parse_document_from_requests(r)
    return doc.xpath('//input[@name="once"]')[0].get('value')

  def login(self, username, password):
    once_value = self.get_once_value()
    post_data = {
      'next': '/',
      'u': username,
      'p': password,
      'once': once_value,
    }
    r = self.request(
      self.login_url, 'POST',
      data = post_data,
    )
    if '/signout?once=' not in r.text:
      raise V2EXFailure('login failed', r)

  def daily_mission(self):
    r = self.request(self.daily_url)
    doc = parse_document_from_requests(r)
    buttons = doc.xpath('//input[@value = "领取 X 铜币"]')
    if not buttons:
      raise V2EXFailure('mission not available', r)

    button = buttons[0]
    url = button.get('onclick').split("'")[1]
    r = self.request(urljoin(self.index_url, url))
    if '已成功领取每日登录奖励' not in r.text:
      raise V2EXFailure('daily mission failed', r)
