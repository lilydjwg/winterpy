'''
utils using GDK
'''

import mimetypes

from gi.repository import Gdk

def get_screen_size():
  screen = Gdk.Screen.get_default()
  return screen.width(), screen.height()

def get_moniter_size(n=0, screen=None):
    if screen is None:
        screen = Gdk.Screen.get_default()
    return Gdk.Screen.get_monitor_workarea(screen, n)

def screenshot(filename, rect=None, filetype=None):
  screen = Gdk.Screen.get_default()
  if rect is None:
    rect = (0, 0, screen.width(), screen.height())
  if filetype is None:
    t = mimetypes.guess_type(filename)[0]
    if t is None:
      raise ValueError('cannot guess filetype for filename: %s' % filename)
    filetype = t.split('/')[1]

  rootwin = screen.get_root_window()
  pixbuf = Gdk.pixbuf_get_from_window(rootwin, *rect)
  pixbuf.savev(filename, filetype, (), ())
