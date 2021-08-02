'''
utils using GDK
'''

import mimetypes

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

def get_screen_size():
  screen = Gdk.Screen.get_default()
  return screen.width(), screen.height()

def get_monitor_size(display=None):
  if display is None:
    display = Gdk.Display.get_default()

  mon = get_mouse_monitor(display)
  return mon.get_workarea()

def get_mouse_monitor(display=None):
  if display is None:
    display = Gdk.Display.get_default()
  seat = display.get_default_seat()
  pointer = seat.get_pointer()
  screen, x, y = pointer.get_position()
  mon = display.get_monitor_at_point(x, y)
  return mon

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
