import os
from time import sleep

import cv2 as cv

import X
import gdkutils

class XAuto:
  _screensize = None

  def __init__(self, tmp_img='/tmp/tmp%d.png' % os.getpid(),
    default_threshold=0.7, default_rect=None):
    self.d = X.Display()
    self.tmp_img = tmp_img
    self.default_threshold = default_threshold
    self.default_rect = default_rect

  def find_and_click(self, *args, back=False, **kwargs):
    pos = self.find(*args, **kwargs)
    if pos:
      if back:
        self.click_and_back(pos)
      else:
        self.click(pos)
    return pos

  def find_and_moveto(self, *args, **kwargs):
    pos = self.find(*args, **kwargs)
    if pos:
      self.moveto(pos)
    return pos

  def click(self, pos=None, button=X.LEFT_BUTTON):
    d = self.d
    if pos is not None:
      d.motion(pos)
    d.button(button)
    d.flush()

  def wait(self, seconds):
    sleep(seconds)

  def click_and_back(self, pos, button=X.LEFT_BUTTON):
    d = self.d
    old_pos = d.getpos()
    d.motion(pos)
    d.button(button)
    d.motion(old_pos)
    d.flush()

  def moveto(self, pos):
    d = self.d
    d.motion(pos)
    d.flush()

  def key(self, keyname):
    d = self.d
    d.key(keyname)
    d.flush()

  def find(self, img, threshold=None, rect=None, repeat=1, interval=0.2):
    if isinstance(img, str):
      img = cv.imread(img, 0)
    if rect is None:
      rect = self.default_rect or (0, 0) + self.screensize
    if threshold is None:
      threshold = self.default_threshold
    tmp_img = self.tmp_img

    for _ in range(repeat):
      gdkutils.screenshot(tmp_img, rect)
      sc = cv.imread(tmp_img, 0)
      res = cv.matchTemplate(img, sc, cv.TM_CCOEFF_NORMED)
      _min_val, max_val, _min_loc, max_loc = cv.minMaxLoc(res)
      similarity = max_val
      x, y = max_loc
      if similarity > threshold:
        x += rect[0]
        y += rect[1]
        x += img.shape[1] // 2
        y += img.shape[0] // 2
        return x, y
      sleep(interval)

    return False

  @property
  def screensize(self):
    return self._screensize or gdkutils.get_screen_size()

  def __del__(self):
    try:
      os.unlink(self.tmp_img)
    except OSError:
      pass

  def monitor_size(self, *args, **kwargs):
    return gdkutils.get_monitor_size(*args, **kwargs)

