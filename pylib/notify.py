#!/usr/bin/env python3
# fileencoding=utf-8

'''
调用 libnotify

TODO：优先级、超时时间等
'''

from ctypes import *

libnotify = CDLL('libnotify.so')
gobj = CDLL('libgobject-2.0.so')

class notify:
  def __init__(self, summary, body=None, icon_str=None):
    libnotify.notify_init("notify-send")
    self.summary = summary.encode()
    if body:
      self.body = body.encode()
    else:
      self.body = None
    if icon_str:
      self.icon_str = icon_str.encode()
    else:
      self.icon_str = None

    self.notify = libnotify.notify_notification_new(c_char_p(self.summary),
        c_char_p(self.body), c_char_p(self.icon_str), c_void_p())

  def show(self):
    libnotify.notify_notification_show(self.notify, c_void_p());

  def update(self, summary=None, body=None, icon_str=None):
    if not any((summary, body)):
      raise TypeError('at least one argument please')

    if summary:
      self.summary = summary.encode()
    if body or body == '':
      self.body = body.encode()
    if icon_str or icon_str == '':
      self.icon_str = icon_str.encode()

    libnotify.notify_notification_update(self.notify, c_char_p(self.summary),
        c_char_p(self.body), c_char_p(self.icon_str), c_void_p())

    self.show()

  def __del__(self):
    try:
      gobj.g_object_unref(self.notify)
      libnotify.notify_uninit()
    except AttributeError:
      # libnotify.so 已被卸载
      pass

  __call__ = update

if __name__ == '__main__':
  from time import sleep
  n = notify('This is a test', '测试一下。')
  n.show()
  sleep(1)
  n.update('再测试一下。')
  del n

