'''
HTTP 会话，主要针对需要登录的服务
'''

import urllib.request
import http.cookiejar
from url import PostData
import os

class Session:
  '''通过 cookie 保持一个 HTTP 会话'''
  UserAgent = None
  def __init__(self, cookiefile='', UserAgent=None, proxy=True):
    '''
    proxy 为 True，使用环境变量，为 dict，作为代理，为假值，不使用代理
    默认使用环境变量
    '''
    self.cookie = http.cookiejar.MozillaCookieJar(cookiefile)
    if os.path.exists(cookiefile):
      self.cookie.load()
    if UserAgent is not None:
      self.UserAgent = UserAgent

    if proxy is True:
      self.urlopener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(self.cookie),
        urllib.request.ProxyHandler(),
      )
    elif isinstance(proxy, dict):
      self.urlopener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(self.cookie),
        urllib.request.ProxyHandler(proxy),
      )
    elif not proxy:
      self.urlopener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(self.cookie),
      )
    else:
      raise ValueError('unexpected proxy value')

  def request(self, url, data=None, timeout=None, headers={}, method=None):
    '''
    发送请求，返回 response 对象

    url 为字符串，data 会传给 PostData
    '''
    kwargs = {}
    # only Python 3.3+ support the method keyword
    if method is not None:
      kwargs['method'] = method

    if data:
      request = urllib.request.Request(url, PostData(data).data, **kwargs)
    else:
      request = urllib.request.Request(url, **kwargs)

    if self.UserAgent:
      request.add_header('User-Agent', self.UserAgent)
    for k, v in headers.items():
      request.add_header(k, v)
    if timeout is None:
      response = self.urlopener.open(request)
    else:
      response = self.urlopener.open(request, timeout=timeout)
    return response

  def __del__(self):
    try:
      self.cookie.save()
    except IOError as e:
      if e.errno != 2:
        raise

class Operation:
  '''与 Session 配合使用，说明一个会话中可能的操作'''
  def login(self, url, logindata, checkfunc):
    '''logindata 是登录字典，checkfunc 返回登录成功与否'''
    logindata = PostData(logindata).data
    response = self.request(url, logindata)
    return checkfunc(response)

  def logout(self):
    '''删除 cookie 好了'''
    os.unlink(self.cookie.filename)

def make_cookie(name, value, expires=None, domain='', path='/'):
  '''
  returns a Cookie instance that you can add to a cookiejar

  expires: the time in seconds since epoch of time
  '''
  return http.cookiejar.Cookie(
    version=0, name=name, value=value, port=None, port_specified=False,
    domain=domain, domain_specified=False, domain_initial_dot=False,
    path=path, path_specified=True, secure=False, expires=expires,
    discard=None, comment=None, comment_url=None, rest={'HttpOnly': None},
    rfc2109=False
  )
