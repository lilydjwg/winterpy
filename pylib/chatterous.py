#!/usr/bin/env python3
# fileencoding=utf-8

'''
会话中的HTTP请求

* GET /go/g/scu_ubuntu/keepalive/?q=1278220713014
* Host: www.chatterous.com
  其中 q 是当前时间
  正常情况下返回 OK.
  每两分钟获取一次

* GET /go/g/scu_ubuntu/members/?q=1278221072912
* Host: www.chatterous.com
  q 依然是当前时间，
  返回一个json，结构如下
    三个数组， admins, members 和 guests，其中对象的属性为
      "contact":  1,
      "username":  "lilybot" ,
      "displayName": "护花使者",
      "user_id": 503516498530199,
      "ignore" : 0
    对于未注册用户，username 为 null
    contact: 1 - 网页，2 - 邮件，3 - Jabber
    ignore: 0, 1
  每10分钟获取一次

* GET /cometd/cometd?message=%5B%7B%22channel%22%3A%22%2Fmeta%2Fconnect%22%2C%22connectionType%22%3A%22callback-polling%22%2C%22clientId%22%3A%22sy7lf68422gmgs3uwb%22%2C%22id%22%3A%2220%22%2C%22timestamp%22%3A%22Sun%2C%2004%20Jul%202010%2005%3A21%3A05%20GMT%22%7D%5D&jsonp=dojo.io.script.jsonp_dojoIoScript21._jsonpCallback
* Host: chatterous.com:7500
  参数 jsonp 不变
  message 是一个 json
    [{"channel":"/meta/connect","connectionType":"callback-polling","clientId":"sy7lf68422gmgs3uwb","id":"20","timestamp":"Sun, 04 Jul 2010 05:21:05 GMT"}]
    id 依次递增
  响应可为
    dojo.io.script.jsonp_dojoIoScript21._jsonpCallback([{"successful":true,"channel":"/meta/connect","id":"20"}])
  可能会有一个 advice 字段，像这样：
    "advice":{"reconnect":"retry","interval":0,"timeout":120000}
  interval 就是下次获取时间间隔，默认为 timeout。为零之后下次就不给出 advice 了。
  出错时会有 error 字段，如 "error":"402::Unknown client"

  通过握手获取 clientId
  message 为
    [{"version":"1.0","minimumVersion":"0.9","channel":"/meta/handshake","id":"0","timestamp":"Sun, 04 Jul 2010 05:51:51 GMT"}]
  响应
    [{"supportedConnectionTypes":["long-polling","callback-polling"],"minimumVersion":"0.9","clientId":"7cmnqobn5l3wg4oplf","successful":true,"channel":"/meta/handshake","id":"0","advice":{"reconnect":"retry","interval":0,"timeout":120000},"version":"1.0"}]
  订阅
  发送 message 为
    [{"channel":"/meta/subscribe","subscription":"/chat/5178515834295","clientId":"7l60jufuc5d2pm6vb2","id":"2","timestamp":"Sun, 04 Jul 2010 13:42:14 GMT"},{"channel":"/meta/subscribe","subscription":"/chat/5306267766771","clientId":"7l60jufuc5d2pm6vb2","id":"3","timestamp":"Sun, 04 Jul 2010 13:42:14 GMT"},{"channel":"/meta/subscribe","subscription":"/chat/5447707406298","clientId":"7l60jufuc5d2pm6vb2","id":"4","timestamp":"Sun, 04 Jul 2010 13:42:14 GMT"},{"channel":"/meta/subscribe","subscription":"/chat/5651502155724","clientId":"7l60jufuc5d2pm6vb2","id":"5","timestamp":"Sun, 04 Jul 2010 13:42:14 GMT"},{"channel":"/meta/subscribe","subscription":"/chat/5649474347272","clientId":"7l60jufuc5d2pm6vb2","id":"6","timestamp":"Sun, 04 Jul 2010 13:42:14 GMT"}]
  回应为
    dojo.io.script.jsonp_dojoIoScript3._jsonpCallback([{"successful":true,"subscription":"/chat/5178515834295","channel":"/meta/subscribe","id":"2"},
    {"subscription":"/chat/5306267766771","successful":true,"channel":"/meta/subscribe","id":"3"},
    {"subscription":"/chat/5447707406298","successful":true,"channel":"/meta/subscribe","id":"4"},
    {"subscription":"/chat/5651502155724","successful":true,"channel":"/meta/subscribe","id":"5"},
    {"subscription":"/chat/5649474347272","successful":true,"channel":"/meta/subscribe","id":"6"}])

  接收消息
    data 可以有多个
    [{"successful":true,"channel":"/meta/connect","id":"31"}, {"data":{"user_id":421027278511291,"user":"supercatexpert@...","ignore":0,"primary_contact_channel":3,"channel_from":"jabber/gtalk","username":null,"role":"member","id":"5178515834295","chat":"我需要日语输入法"},"channel":"/chat/5178515834295"}]

  发送消息
    POST /go/g/scu_ubuntu/post/
    Host: www.chatterous.com
  参数
    msg 消息
  响应
    OK.


在通讯过程中也可能要重新握手
  dojo.io.script.jsonp_dojoIoScript37._jsonpCallback([{"error":"402::Unknown client","successful":false,"channel":"/meta/connect","advice":{"reconnect":"handshake","interval":500}}])

'''

import os, sys, re
from url import URL, Cookie, URIescape, URIunescape
from getpass import getpass
import urllib.request
import json
import threading
import time, datetime

# 一些设置
cookieFile = os.path.expanduser('~/.chatterous/cookies')
plugin_dir = '~/.chatterous/plugins'

new_group = re.compile(r"new Chatterous.GroupTab\('(?P<name>[^']+)', '(?P<id>[^']+)','[^']+'")
group_chat = re.compile(r"window.groupEventManager.registerGroup\('(?P<id>[^']+)', '(?P<chat>[^']+)'\)")

class Request:
  def __init__(self, cookie=None):
    self.post = ''
    self.cookie = Cookie(cookie)

  def login(self, user, passwd):
    '''登录'''
    request = urllib.request.Request('https://www.chatterous.com/accounts/login/')
    request.add_header('User-Agent',  'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6')
    response = urllib.request.urlopen(request, timeout=10)
    self.cookie.addFromResponse(response)

    self.addpost('username', user)
    self.addpost('password', passwd)
    self.addpost('next', '')
    request = urllib.request.Request('https://www.chatterous.com/accounts/login/')
    request.add_header('User-Agent',  'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6')
    request.add_header('Cookie', self.cookie.sendFormat())
    response = urllib.request.urlopen(request, data=self.post, timeout=10)
    self.cookie.addFromResponse(response)
    if '<a href="/accounts/logout/">sign out</a>' in response.read().decode('utf-8'):
      return True
    else:
      return False

  def open(self, url, data=None):
    '''打开 url'''
    request = urllib.request.Request(url, data=data)
    request.add_header('User-Agent',  'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6')
    request.add_header('Cookie', self.cookie.sendFormat())
    response = urllib.request.urlopen(request, timeout=125)
    return response

  def save(self, file):
    '''将 cookie 保存到文件'''
    open(file, 'w').write(str(self.cookie))
    os.chmod(file, 0o600)
    self.cookie.file = None

  def addpost(self, key, value):
    self.post += '&'+key+'='+value if self.post else key+'='+value

  def __del__(self):
    self.save(cookieFile)

class Chatterous:
  _id = -1 #报文 id
  def __init__(self, user):
    self.r = Request(cookie=cookieFile)
    self.user = user
    r = self.r.open('http://www.chatterous.com/go/groups/')
    res = r.read().decode('utf-8')
    if '<a href="/accounts/logout/">sign out</a>' not in res:
      while not self.r.login(user, getpass('%s 的密码: ' % user)):
        pass

    groups = []
    for m in new_group.finditer(res):
      groups.append({'id': m.group('id'), 'name': m.group('name')})
    i = 0
    for m in group_chat.finditer(res):
      groups[i]['chat'] = m.group('chat')
      i += 1
    self.groups = {}
    for x in groups:
      self.groups[x['id']] = {'chat': x['chat'], 'name': x['name']}

  def getmembers(self, group):
    r = self.r.open('http://www.chatterous.com/go/g/%s/members/?q=%d' % (
      group, self.gettimestamp()))
    group = self.groups[group]
    group['members'] = json.loads(r.read().decode('utf-8'))

  def sendmsg(self, group, msg):
    res = self.r.open('http://www.chatterous.com/go/g/%s/post/' % group,
        data='msg=%s'%URIescape(msg)).read().decode('utf-8')
    return res == 'OK.'

  def gettimestamp(self):
    return int(time.time()*1000)

  def getcurtime(self):
    d = datetime.datetime.now()
    d += datetime.timedelta(hours=-8)
    return d.strftime('%a, %d %b %Y %H:%M:%S GMT')

  def handshake(self):
    url = 'http://chatterous.com:7500/cometd/cometd'
    url += '?jsonp=dojo.io.script.jsonp_dojoIoScript1._jsonpCallback'
    url += '&message='
    url += URIescape('[{"version":"1.0","minimumVersion":"0.9","channel":"/meta/handshake","id":"%d","timestamp":"%s"}]' % (
      self.id, self.getcurtime()))
    res = self.r.open(url).read().decode('utf-8')
    res = res[res.find('(')+1:-3] #-3: )\r\n
    res = json.loads(res)[0]
    if res['successful']:
      self.clientId = res['clientId']
    else:
      raise ChatterousError('handshake failed')
    return res

  def checkgroup(self, groups):
    '''如果组信息不存在，尝试打开相应页面以获取之'''
    def open(group):
      print('Get group', group)
      self.r.open('http://www.chatterous.com/%s/' % group).read()

    threads = []
    for group in groups:
      if group not in self.groups:
        th = threading.Thread(target=open, args=(group,))
        th.daemon = True
        th.start()
        threads.append(th)
    for th in threads:
      if th.is_alive():
        th.join()

    if threads:
      r = self.r.open('http://www.chatterous.com/go/groups/')
      res = r.read().decode('utf-8')
      groups = []
      for m in new_group.finditer(res):
        groups.append({'id': m.group('id')})
      i = 0
      for m in group_chat.finditer(res):
        groups[i]['chat'] = m.group('chat')
        i += 1
      self.groups = {}
      for x in groups:
        self.groups[x['id']] = {'chat': x['chat']}

  def subscribe(self, groups=None):
    if groups is None:
      groups = list(self.groups.keys())
    elif isinstance(groups, str):
      groups = [groups]
    id = self.id

    url = 'http://chatterous.com:7500/cometd/cometd'
    url += '?jsonp=dojo.io.script.jsonp_dojoIoScript%d._jsonpCallback' % (id+1)
    url += '&message='
    message = [self.subscribe_group2dict(x) for x in groups]
    url += URIescape(json.dumps(message))
    res = self.r.open(url).read().decode('utf-8')
    res = res[res.find('(')+1:-3] #-3: )\r\n
    res = json.loads(res)[0]
    return res

  def recvmsg(self):
    url = 'http://chatterous.com:7500/cometd/cometd'
    id = self.id
    url += '?jsonp=dojo.io.script.jsonp_dojoIoScript%d._jsonpCallback' % (id+1)
    url += '&message='
    url += URIescape('[{"channel":"/meta/connect","connectionType":"callback-polling","clientId":"%s","id":"%d","timestamp":"%s"}]' % (
      self.clientId, id, self.getcurtime()))
    res = self.r.open(url).read().decode('utf-8')
    res = res[res.find('(')+1:-3] #-3: )\r\n
    res = json.loads(res)
    #TODO 对握手失败的判断
    if not res[0]['successful']:
      raise ChatterousError('connect failed')
    return res

  @property
  def id(self):
    self._id += 1
    return self._id

  def subscribe_group2dict(self, group):
    '''把组映射到字典以便转换成 json，用于 subscribe'''
    ret = {"channel": "/meta/subscribe", "clientId": self.clientId}
    ret['subscription'] = "/chat/%s" % self.groups[group]['chat']
    ret['timestamp'] = self.getcurtime()
    return ret

class ChatterousError(Exception):
  pass

