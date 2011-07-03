#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
金山快盘 之 python 版

2010年11月21日

file 包含的属性
  type:       file, folder
  name:       文件名
  fileId
  size
  createdTime
  modTime
  parentId:   无则为空字典
  fileVer
  opVer
  sha1:       文件夹为空字典
  shared

共享根目录包含一个 sharer 属性
  nickname
  right 权限(read, write)
  userId
  email
'''

from httpsession import Session, Operation
from getpass import getpass
from lilypath import path, sha1path
from url import Cookie, URIescape, encode_multipart_formdata
from myutils import filesize
import json
import sys
from datetime import datetime

class kpath(sha1path):
  '''金山快盘的路径'''
  def __init__(self, kf, ids):
    '''ids 是一个字典，完成 fileId 到 文件 的映射'''
    self.data = kf
    self.ids = ids
  def __str__(self):
    return self.data['name']
  @property
  def mtime(self):
    return datetime.strptime(self.data['modTime'], '%Y-%m-%d %H:%M:%S')
  @property
  def size(self):
    return int(self.data['size'])
  def parent(self):
    return self.__class__(ids[self.data['parentId']], self.ids)
  def list(self):
    return [self.__class__(x, self.ids) for x in self.data['children']]
  def dirs(self):
    return [x for x in self.list() if x.isdir()]
  def files(self):
    return [x for x in self.list() if x.isfile()]
  def isfile(self):
    return self.data['type'] == 'file'
  def isdir(self):
    return self.data['type'] == 'folder'
  def sha1(self):
    if self.isdir():
      raise IOError(21, "Is a directory: '%s'" % self.data['name'])
    return self.data['sha1']
  def exists(self):
    return True
  def mappath(self, root):
    '''映射到磁盘路径（同步时用）
    root 为 path 对象'''
    if self.hasParent():
      return self.parent().mappath(root) + self.data['name']
    else:
      return root + self.data['name']
  def _notimplement(self, *args, **kwargs):
    raise NotImplementedError
  #未实现的有破坏性的操作
  mkdir = rename = copy = open = unlink = rmdir = _notimplement

class KSession(Session, Operation):
  mainurl = 'http://k.wps.cn/fileviewer/'
  needlogin_redir = 'http://k.wps.cn/login/'
  loginurl = 'http://k.wps.cn/login/?act=login'
  UserAgent = 'Long Live Linux'

  def __init__(self, username, cookiefile):
    Session.__init__(self, cookiefile)
    self.username = username
    res = self.request(self.mainurl)
    checklogin = lambda response: response.geturl().find('login') == -1
    if not checklogin(res):
      loggedin = False
      while not loggedin:
        password = getpass('请输入 %s 的密码: ' % self.username)
        if not password:
          print('放弃登录')
          return
        logindata = {
          'access': '',
          'app': '',
          'clientHardId': '',
          'clientName': '',
          'clientVer': '',
          'rememberme': '1',
          'to': '',
          'userName': self.username,
          'userPassword': password,
        }
        loggedin = self.login(self.loginurl, logindata, checklogin)

  def list(self, id='root'):
    return self.post('list', {'id': id})['file']

  def getsharetome(self):
    return self.post('listallshare', {'type': 'ToMe'})['file']

  def getsharetoothers(self):
    return self.post('listallshare', {'type': 'out'})['file']

  def delete(self, file):
    return self.post('delete', {'fileId[]': file['fileId']})

  def upload(self, file, parentId='root'):
    '''
    file 为 path 对象

    注意：不能用于上传大文件
    '''
    result = self.post('newfile', {
      'size': str(file.size),
      'parentId': parentId,
      'name': file.basename})

    fields = (
          ('Filename', file.basename),
          ('size', str(file.size)),
          ('fileId', result['fileId']),
          ('flashId', '2ee86160c6f9496cb6238ee9161f4755-178684278'),
          ('Upload', 'Submit Query'),
        )
    contenttype, data = encode_multipart_formdata(fields,
        [('Filedata', file.basename, file.open(encoding='latin1').read())])
    return self.post('upload', data, headers={'Content-Type': contenttype})

  def download(self, file, dir):
    '''
    将文件下载到指定目录，会在终端显示下载状态
    file 是快盘的 dict，而 dir 是 path 对象
    '''
    # url = self.getdownloadurl(file['fileId'])
    url = self.mainurl+ 'download/?fileId=%s&uname=%s' % (file['fileId'], URIescape(file['name']))
    res = self.request(url)
    size = int(file['size'])
    oldpercent = percent = 0
    print('下载 %s，总大小：%s' % (file['name'], filesize(size)))
    with (dir+file['name']).open('wb') as f:
      data = res.read(4096)
      while data:
        f.write(data)
        percent = 100 * f.tell() // size
        if percent - oldpercent > 4:
          print('%d%%...' % percent, end='')
          sys.stdout.flush()
          oldpercent = percent
        data = res.read(4096)
    if oldpercent != 100:
      print('100%', end='')
    print('\n%s 下载完成' % file['name'])

  def createdir(self, dirName, parentId=''):
    '''parentId 为 '' 则为 root'''
    return self.post('createdir', {'dirName': dirName, 'parentId': parentId})

  def getdownloadurl(self, fileId):
    result = self.post('requestdownload', {'fileId': fileId })
    result['fileName'] = URIescape(result['fileName'])
    return '{r[url]}stub={r[stub]}&uname={r[fileName]}'.format(r=result)

  def post(self, loc, arg, headers={}):
    res = self.request(self.mainurl+loc+'/', arg, headers=headers)
    result = json.loads(res.read().decode('utf-8'))
    return result

class KuaipanException(Exception):
  def __init__(self, msg):
    self.msg = msg
  def __str__(self):
    return str(self.msg)

def getTree(shares):
  '''从共享文件列表生成共享树
  注意返回的是共享树根的列表和一个 fileId 映射表'''
  ids = {}
  for i in shares:
    ids[i['fileId']] = i
    # 所有目录都有子项
    if i['type'] == 'folder':
      i['children'] = []

  root = []
  for i in shares:
    pid = i['parentId']
    if pid:
      ids[pid]['children'].append(i)
    else:
      root.append(i)

  return root, ids

def traverse(dir, p=sha1path()):
  '''遍历金山快盘的文件树，返回 文件 和 目录(sha1path对象)'''
  for i in dir['children']:
    if i['type'] == 'folder':
      for j in traverse(i, p+i['name']):
        yield j
    else:
      yield i, p
