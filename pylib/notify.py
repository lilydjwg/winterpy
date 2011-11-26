'''
调用 libnotify
'''

from ctypes import *
from threading import Lock

NOTIFY_URGENCY_LOW = 0
NOTIFY_URGENCY_NORMAL = 1
NOTIFY_URGENCY_CRITICAL = 2
UrgencyLevel = {NOTIFY_URGENCY_LOW, NOTIFY_URGENCY_NORMAL, NOTIFY_URGENCY_CRITICAL}

libnotify = CDLL('libnotify.so')
gobj = CDLL('libgobject-2.0.so')
libnotify_lock = Lock()
libnotify_inited = 0

class notify:
  def __init__(self, summary='', body=None, icon_str=None, name="pynotify"):
    '''optional `name' is used as the app name when init the library'''
    global libnotify_inited
    with libnotify_lock:
      if not libnotify_inited:
        libnotify.notify_init(name)
      libnotify_inited += 1

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

  def set_timeout(self, timeout):
    '''set `timeout' in milliseconds'''
    libnotify.notify_notification_set_timeout(self.notify, int(timeout))

  def set_urgency(self, urgency):
    if urgency not in UrgencyLevel:
      raise ValueError
    libnotify.notify_notification_set_urgency(self.notify, urgency)

  def __del__(self):
    try:
      gobj.g_object_unref(self.notify)

      global libnotify_inited
      with libnotify_lock:
        libnotify_inited -= 1
        if not libnotify_inited:
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

