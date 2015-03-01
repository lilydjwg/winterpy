'''
utils using GDK
'''

import mimetypes

from gi.repository import Gdk

def get_screen_size():
  screen = Gdk.Screen.get_default()
  return screen.width(), screen.height()

def get_monitor_size(n=None, screen=None):
  if screen is None:
    screen = Gdk.Screen.get_default()

  if n is None:
    n = get_mouse_monitor()

  return Gdk.Screen.get_monitor_workarea(screen, n)

def get_mouse_monitor(display=None):
  if display is None:
    display = Gdk.Display.get_default()
  screen, x, y, _ = Gdk.Display.get_pointer(display)
  return Gdk.Screen.get_monitor_at_point(screen, x, y)

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
  pixbuf.save(filename, filetype, (), ())
