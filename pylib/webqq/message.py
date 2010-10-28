#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''(已废弃)'''
import collections
import time
from urllib.parse import unquote as URIunescape

import logging
def getLogger():
  '''
  10 DEBUG 原始消息/调试信息
  15 EVENT 事件发生了
  20 INFO  消息干了什么
  25 NOTE  注意了
  '''
  EVENT = 15
  NOTE = 25
  logging.addLevelName(EVENT, 'EVENT')
  logging.addLevelName(NOTE, 'NOTE')
  class Logger(logging.getLoggerClass()):
    def event(self, msg, *args, **kwargs):
      if self.isEnabledFor(EVENT):
        self._log(EVENT, msg, args, **kwargs)
    def note(self, msg, *args, **kwargs):
      if self.isEnabledFor(NOTE):
        self._log(NOTE, msg, args, **kwargs)
  logging.setLoggerClass(Logger)

  logger = logging.getLogger('webqq.message')
  logger.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(levelname)s:%(name)s:%(funcName)s %(message)s')
  ch.setFormatter(formatter)
  logger.addHandler(ch)

  return logger

logger = getLogger()

状态 = {
    '10': '在线',
    '20': '离线',
    '30': '离开',
    '40': '隐身',
    }
客户端 = ['', '手机QQ', 'WebQQ', '桌面版QQ']

class QQMessageCommon:
  '''发送和接收消息类的父类

  listeners 
    事件-函数列表 字典，保存了通过 addEventListener 添加了事件处理函数
  preventDefault
    是否执行默认事件的 事件-布尔值 字典
  '''
  listeners = collections.defaultdict(list)
  preventDefault = collections.defaultdict(lambda: False)
  msgid = 0
  def newmsg(self, string):
    self.source = string
    if self.dir == 'sent':
      self.trigger('RawMsgSent')
    elif self.dir == 'recved':
      self.trigger('RawMsgRecved')
    else:
      raise Exception('未知的方向 %s' % self.dir)

    msg = self.preproc(string)
    if not msg: # 没有消息
      return
    try:
      self.handleByType(msg[1], msg[2:])
    except IndexError:
      print('IndexError: ', end='')
      print(msg)
  def handleByType(self, type, msg):
    '''按类型分发'''
    handler = 'type' + type
    if hasattr(self, handler):
      getattr(self, handler)(msg)
    else:
      logger.warn('未知类型：%s，方向是 %s', type, self.dir)
  def trigger(self, event, **kwargs):
    '''按事件分发'''
    logger.event(event)

    # 通过 addEventListener 添加的函数
    for f in self.listeners[event]:
      f(self, event=event, **kwargs)

    # 默认动作
    if self.preventDefault[event]:
      pass
    else:
      if hasattr(self, event):
        getattr(self, event)(**kwargs)
      else:
        logger.warn('未预定义的事件：%s', event)

  def addEventListener(self, event, func, allowMultiple=False):
    '''添加事件处理函数
    如果不指定 allowMultiple 为 True 并且处理函数已经存在，返回 False。成功添
    加返回 True。'''
    if not hasattr(func, '__call__'):
      raise ValueError('func 不是函数')

    listeners = self.listeners[event]
    if not allowMultiple and func in listeners:
      return False
    listeners.append(func)
    return True

  def preproc(self, msg):
    '''预处理消息字符串，主要是分解各部分'''
    if not msg.strip(): # 空回答
      self.trigger('EmptyAnswer')
      return []
    # 有时两条消息会一起发出，中间以 \x1d 隔开这时应该逐个处理
    if '\x1d' in msg:
      raise ValueError(r'含有多条以 \x1d 分隔的消息。请分别处理。')
    l = msg.split(';')
    self.MyQQNumber = l[0]
    return l
  def EmptyAnswer(self, **msg):
    '''收到空的回应'''
    logger.info('空回应')
  def __call__(self, *args, **kwargs):
    # 这里不能直接赋值，因为 newmsg 方法可能是子类的
    self.newmsg(*args, **kwargs)

class QQMessageSent(QQMessageCommon):
  dir = 'sent'
  def type00(self, msg):
    self.msgid = int(msg[0])
    self.sessionid = msg[1]
    self.trigger('HeartBeat')
  def type17(self, msg):
    # TODO 未分析完全
    self.msgid = int(msg[0])
    self.sessionid = msg[1]
    if msg[5] == '1': #好友消息
      self.trigger('MessageRecvedOK', RemoteQQ=msg[2])
    elif msg[5] == '2': #群消息
      self.trigger('GroupMessageRecvedOK')
    else:
      logger.warn('未处理完的 17 类型')
  def type0d(self, msg):
    self.msgid = int(msg[0])
    self.sessionid = msg[1]
    self.trigger('StatusChange', Status=msg[2])
  def type16(self, msg):
    # TODO 未分析完全
    self.msgid = int(msg[0])
    self.sessionid = msg[1]
    if msg[3] == '0b' and msg[4] == '132':
      message = URIunescape(msg[5])
      fontstr = URIunescape(msg[6])
      self.trigger('MessageSent', RemoteQQ=msg[2], Message=message,
          FontString=fontstr)
    else:
      logger.warn('未处理完的 16 类型')
  def HeartBeat(self, **msg):
    logger.info('Heart beat')
  def GroupMessageRecvedOK(self, **msg):
    #TODO 哪条消息呢？
    logger.info('群消息已收到')
  def RawMsgSent(self, **msg):
    logger.debug('发送消息 %s', self.source)
  def StatusChange(self, **msg):
    logger.info('改变状态为 %s', 状态[msg['Status']])
  def MessageRecvedOK(self, **msg):
    logger.info('来自 %s 的消息已收到', msg['RemoteQQ'])
  def MessageSent(self, **msg):
    logger.info('发送消息到 %s：%s, 使用字体 %s',
        msg['RemoteQQ'], msg['Message'], msg['FontString'])
class QQMessageRecved(QQMessageCommon):
  dir = 'recved'
  recvid = 0
  def type02(self, msg):
    # msg[1] 总是 0
    self.msgid = int(msg[0])
    if msg[1] != '0':
      logger.warn('心跳回应的第一个字段改变为 %s！', msg[1])
    self.time = msg[2]
    self.trigger('HeartBeatOK')
  def type0d(self, msg):
    self.msgid = int(msg[0])
    if msg[1] != '0':
      logger.warn('状态更改回应的最后一个字段改变为 %s！', msg[1])
    self.trigger('StatusChangeOK')
  def type17(self, msg):
    # TODO 未分析完全
    recvid = int(msg[0])
    if recvid == self.recvid:
      logger.note('相同的 recvid 被抛弃')
      return

    self.recvid = recvid
    if msg[3] == '09' and msg[4] == '0b':
      message = URIunescape(msg[5])
      self.trigger('MessageRecved', RemoteQQ=msg[1], Message=message,
          FontString=msg[6], TimeStramp=float(msg[7]))
    elif msg[3] == '2b' and msg[4] == '0b': #群消息
      message = URIunescape(msg[5])
      self.trigger('GroupMessageRecved', RemoteQQ=msg[9], Message=message,
          FontString=msg[6], TimeStramp=float(msg[12]), GroupNo=msg[8])
    else:
      logger.warn('未处理完的 17 类型')
  def type16(self, msg):
    self.msgid = int(msg[0])
    if msg[1] != '0':
      logger.warn('状态更改回应的最后一个字段改变为 %s！', msg[1])
    self.trigger('MessageSentOK')
  def type67(self, msg):
    self.msgid = int(msg[0])
    if msg[1] != '03':
      logger.warn('查询签名结果的第二个字段改变为 %s！', msg[1])
    if msg[2] != '0':
      logger.warn('查询签名结果的第三个字段改变为 %s！', msg[1])
    # MaxQQ = str(int(msg[3]+1)) #XXX 谁能告诉我这个是做什么用的？
    nos = msg[4::2]
    sigs = msg[5::2]
    Signatures = dict(zip(nos, sigs))
    self.trigger('SignatureResult', Signatures=Signatures)
  def type81(self, msg):
    self.recvid = int(msg[0])
    self.trigger('BuddyStatus', RemoteQQ=msg[1], Status=msg[2],
        ClientType=int(msg[3]))
  def BuddyStatus(self, **msg):
    logger.info('%s 的状态为 %s，使用 %s',
        msg['RemoteQQ'], 状态[msg['Status']], 客户端[msg['ClientType']] or '未知')
  def GroupMessageRecved(self, **msg):
    logger.info('收到来自 %s 的群消息 %s, 使用字体 %s，时间为 %s，群号是 %s',
        msg['RemoteQQ'], msg['Message'], msg['FontString'],
        time.ctime(msg['TimeStramp']), msg['GroupNo'])
  def HeartBeatOK(self, **msg):
    logger.info('Heart beated')
  def RawMsgRecved(self, **msg):
    logger.debug('接收消息 %s', self.source)
  def MessageRecved(self, **msg):
    logger.info('收到来自 %s 的消息 %s, 使用字体 %s，时间为 %s',
        msg['RemoteQQ'], msg['Message'], msg['FontString'],
        time.ctime(msg['TimeStramp']))
  def MessageSentOK(self, **msg):
    logger.info('消息发送成功')
  def SignatureResult(self, **msg):
    m = []
    for i in msg['Signatures'].items():
      m.append('%s 的签名是：%s' % i)
    logger.info('\n'.join(m))
  def StatusChangeOK(self, **msg):
    logger.info('改变状态成功')
class QQMessageHandler:
  def __init__(self, sentHandler=QQMessageSent, recvedHandler=QQMessageRecved):
    '''返回消息处理函数，其参数为 消息字符串 和 方向'''
    self.sentHandler = sentHandler()
    self.recvedHandler = recvedHandler()

  def __call__(self, msg, dir):
    if dir == 'sent':
      self.sentHandler(msg)
    elif dir == 'recved':
      self.recvedHandler(msg)
    else:
      raise ValueError('dir 取值应为 sent 或 recved')
