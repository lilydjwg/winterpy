#!/usr/bin/env python3
# vim:fileencoding=utf-8

import os
from time import sleep

from myopencv import Image
import X
import gdkutils

class XAuto:
  _screensize = None

  def __init__(self, tmp_img='/dev/shm/tmp%d.png' % os.getpid(),
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

  def click(self, pos, button=X.LEFT_BUTTON):
    d = self.d
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
      img = Image(img)
    if rect is None:
      rect = self.default_rect or (0, 0) + self.screensize
    if threshold is None:
      threshold = self.default_threshold
    tmp_img = self.tmp_img

    for _ in range(repeat):
      gdkutils.screenshot(tmp_img, rect)
      sc = Image(tmp_img)
      (x, y), similarity = sc.match(img)
      if similarity > threshold:
        x += rect[0]
        y += rect[1]
        x += img.width // 2
        y += img.height // 2
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

