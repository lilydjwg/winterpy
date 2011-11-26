'''
HTTP 会话，主要针对需要登录的服务

2010年10月22日
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

  def request(self, url, data=None, timeout=None, headers={}):
    '''
    发送请求，返回 response 对象

    url 为字符串，data 会传给 PostData
    '''
    if data:
      request = urllib.request.Request(url, PostData(data).data)
    else:
      request = urllib.request.Request(url)

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

