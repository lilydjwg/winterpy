from PyPDF2.generic import (
  StreamObject, NameObject, NumberObject, DictionaryObject,
  DecodedStreamObject,
)
from PyPDF2.filters import FlateDecode

MODE_TO_COLORSPACE = {
  'RGB': (8, '/DeviceRGB'),
  'L': (8, '/DeviceGray'),
  'CMYK': (8, '/DeviceCMYK'),
}

class PdfImageFromPillow(StreamObject):
  def __init__(self, im):
    super().__init__()
    try:
      depth, colorspace = MODE_TO_COLORSPACE[im.mode]
    except KeyError:
      raise NotImplementedError('image mode %r not supported' % im.mode)
    w, h = im.size
    # always compress raw image data
    self._data = FlateDecode.encode(im.tobytes())
    self[NameObject("/Filter")] = NameObject('/FlateDecode')
    self[NameObject('/Type')] = NameObject('/XObject')
    self[NameObject('/Subtype')] = NameObject('/Image')
    self[NameObject('/Width')] = NumberObject(w)
    self[NameObject('/Height')] = NumberObject(h)
    self[NameObject('/BitsPerComponent')] = NumberObject(depth)
    self[NameObject('/ColorSpace')] = NameObject(colorspace)

def add_xobject_to_page(page, obj_id):
  res = page.setdefault(NameObject('/Resources'), DictionaryObject())
  xo = res.setdefault(NameObject('/XObject'), DictionaryObject())
  seq = 0
  while True:
    name = NameObject('/img_%s' % seq)
    if name not in xo:
      xo[name] = obj_id
      return name
    seq += 1

class ImageManager:
  def __init__(self, pagesize):
    self.cmds = []
    self.w, self.h = pagesize

  def __enter__(self):
    cmds = self.cmds
    cmds.append('q')
    # 向上移动一个页面的高度，使得原点位于左上角
    cm = '1 0 0 1 0 %s cm' % self.h
    cmds.append(cm)
    # 翻转，使得 y 轴向下
    cm = '1 0 0 -1 0 0 cm'
    cmds.append(cm)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.cmds.append('Q')

  def put_image(self, name, coordinate, size):
    cmds = self.cmds
    cmds.append('q')
    cm = '1 0 0 1 %s %s cm' % coordinate
    cmds.append(cm)
    cm = '%s 0 0 %s 0 0 cm' % size
    cmds.append(cm)
    cmds.append('%s Do' % name)
    cmds.append('Q')

  def tobytes(self):
    return '\n'.join(self.cmds).encode('ascii')

def flate_string(s):
  o = DecodedStreamObject()
  o.setData(s)
  return o.flateEncode()
