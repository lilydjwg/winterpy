#!/usr/bin/env python
# coding=utf-8

'''
Python2 程序，为Vim的图形界面配色方案增加终端（256色）版
http://www.vim.org/scripts/script.php?script_id=2778

2010年6月11日
'''

import os, sys, re
import distutils.file_util
import colorsys

termcolor = { 16: '#000000',
    17: '#00005f',
    18: '#000087',
    19: '#0000af',
    20: '#0000d7',
    21: '#0000ff',
    22: '#005f00',
    23: '#005f5f',
    24: '#005f87',
    25: '#005faf',
    26: '#005fd7',
    27: '#005fff',
    28: '#008700',
    29: '#00875f',
    30: '#008787',
    31: '#0087af',
    32: '#0087d7',
    33: '#0087ff',
    34: '#00af00',
    35: '#00af5f',
    36: '#00af87',
    37: '#00afaf',
    38: '#00afd7',
    39: '#00afff',
    40: '#00d700',
    41: '#00d75f',
    42: '#00d787',
    43: '#00d7af',
    44: '#00d7d7',
    45: '#00d7ff',
    46: '#00ff00',
    47: '#00ff5f',
    48: '#00ff87',
    49: '#00ffaf',
    50: '#00ffd7',
    51: '#00ffff',
    52: '#5f0000',
    53: '#5f005f',
    54: '#5f0087',
    55: '#5f00af',
    56: '#5f00d7',
    57: '#5f00ff',
    58: '#5f5f00',
    59: '#5f5f5f',
    60: '#5f5f87',
    61: '#5f5faf',
    62: '#5f5fd7',
    63: '#5f5fff',
    64: '#5f8700',
    65: '#5f875f',
    66: '#5f8787',
    67: '#5f87af',
    68: '#5f87d7',
    69: '#5f87ff',
    70: '#5faf00',
    71: '#5faf5f',
    72: '#5faf87',
    73: '#5fafaf',
    74: '#5fafd7',
    75: '#5fafff',
    76: '#5fd700',
    77: '#5fd75f',
    78: '#5fd787',
    79: '#5fd7af',
    80: '#5fd7d7',
    81: '#5fd7ff',
    82: '#5fff00',
    83: '#5fff5f',
    84: '#5fff87',
    85: '#5fffaf',
    86: '#5fffd7',
    87: '#5fffff',
    88: '#870000',
    89: '#87005f',
    90: '#870087',
    91: '#8700af',
    92: '#8700d7',
    93: '#8700ff',
    94: '#875f00',
    95: '#875f5f',
    96: '#875f87',
    97: '#875faf',
    98: '#875fd7',
    99: '#875fff',
    100: '#878700',
    101: '#87875f',
    102: '#878787',
    103: '#8787af',
    104: '#8787d7',
    105: '#8787ff',
    106: '#87af00',
    107: '#87af5f',
    108: '#87af87',
    109: '#87afaf',
    110: '#87afd7',
    111: '#87afff',
    112: '#87d700',
    113: '#87d75f',
    114: '#87d787',
    115: '#87d7af',
    116: '#87d7d7',
    117: '#87d7ff',
    118: '#87ff00',
    119: '#87ff5f',
    120: '#87ff87',
    121: '#87ffaf',
    122: '#87ffd7',
    123: '#87ffff',
    124: '#af0000',
    125: '#af005f',
    126: '#af0087',
    127: '#af00af',
    128: '#af00d7',
    129: '#af00ff',
    130: '#af5f00',
    131: '#af5f5f',
    132: '#af5f87',
    133: '#af5faf',
    134: '#af5fd7',
    135: '#af5fff',
    136: '#af8700',
    137: '#af875f',
    138: '#af8787',
    139: '#af87af',
    140: '#af87d7',
    141: '#af87ff',
    142: '#afaf00',
    143: '#afaf5f',
    144: '#afaf87',
    145: '#afafaf',
    146: '#afafd7',
    147: '#afafff',
    148: '#afd700',
    149: '#afd75f',
    150: '#afd787',
    151: '#afd7af',
    152: '#afd7d7',
    153: '#afd7ff',
    154: '#afff00',
    155: '#afff5f',
    156: '#afff87',
    157: '#afffaf',
    158: '#afffd7',
    159: '#afffff',
    160: '#d70000',
    161: '#d7005f',
    162: '#d70087',
    163: '#d700af',
    164: '#d700d7',
    165: '#d700ff',
    166: '#d75f00',
    167: '#d75f5f',
    168: '#d75f87',
    169: '#d75faf',
    170: '#d75fd7',
    171: '#d75fff',
    172: '#d78700',
    173: '#d7875f',
    174: '#d78787',
    175: '#d787af',
    176: '#d787d7',
    177: '#d787ff',
    178: '#d7af00',
    179: '#d7af5f',
    180: '#d7af87',
    181: '#d7afaf',
    182: '#d7afd7',
    183: '#d7afff',
    184: '#d7d700',
    185: '#d7d75f',
    186: '#d7d787',
    187: '#d7d7af',
    188: '#d7d7d7',
    189: '#d7d7ff',
    190: '#d7ff00',
    191: '#d7ff5f',
    192: '#d7ff87',
    193: '#d7ffaf',
    194: '#d7ffd7',
    195: '#d7ffff',
    196: '#ff0000',
    197: '#ff005f',
    198: '#ff0087',
    199: '#ff00af',
    200: '#ff00d7',
    201: '#ff00ff',
    202: '#ff5f00',
    203: '#ff5f5f',
    204: '#ff5f87',
    205: '#ff5faf',
    206: '#ff5fd7',
    207: '#ff5fff',
    208: '#ff8700',
    209: '#ff875f',
    210: '#ff8787',
    211: '#ff87af',
    212: '#ff87d7',
    213: '#ff87ff',
    214: '#ffaf00',
    215: '#ffaf5f',
    216: '#ffaf87',
    217: '#ffafaf',
    218: '#ffafd7',
    219: '#ffafff',
    220: '#ffd700',
    221: '#ffd75f',
    222: '#ffd787',
    223: '#ffd7af',
    224: '#ffd7d7',
    225: '#ffd7ff',
    226: '#ffff00',
    227: '#ffff5f',
    228: '#ffff87',
    229: '#ffffaf',
    230: '#ffffd7',
    231: '#ffffff',
    232: '#080808',
    233: '#121212',
    234: '#1c1c1c',
    235: '#262626',
    236: '#303030',
    237: '#3a3a3a',
    238: '#444444',
    239: '#4e4e4e',
    240: '#585858',
    241: '#626262',
    242: '#6c6c6c',
    243: '#767676',
    244: '#808080',
    245: '#8a8a8a',
    246: '#949494',
    247: '#9e9e9e',
    248: '#a8a8a8',
    249: '#b2b2b2',
    250: '#bcbcbc',
    251: '#c6c6c6',
    252: '#d0d0d0',
    253: '#dadada',
    254: '#e4e4e4',
    255: '#eeeeee' }

def _(str):
  return str

# 一些全局变量
by = _('本配色方案由 gui2term.py 程序增加彩色终端支持。')
cfg = '231'
cbg = '16'
wd = os.path.dirname(os.path.abspath(sys.argv[0]))
if os.path.isfile('rgb.txt'):
  rgbfile = 'rgb.txt'
elif os.path.isfile(os.path.join(wd, 'rgb.txt')):
  rgbfile = os.path.join(wd, 'rgb.txt')
else:
  rgbfile = '/usr/share/vim/vim72/rgb.txt'
name2hex = {}
groups = {}
re_hexcolor = re.compile('^#[0-9a-fA-F]{6}$')
re_hiline = re.compile('^\s*hi\w*\s+[A-Z]\w+')
re_name = re.compile('(?<=\s)[A-Z]\w+(?=\s+gui)')
class color:
  def __init__(self, r=0, g=0, b=0):
    self.r = r
    self.g = g
    self.b = b

  # 此计算比较耗时，因此不在 __init__ 里计算
  def rgb2xterm(self):
    '''selects the nearest xterm color for a rgb value ('color' class)'''
    # TODO 更好的计算法
    best_match= 0
    smallest_distance = 10000000
    for c in range(16,255):
      # d = (int(termcolor[c][1:3], 16) - self.r) ** 2 + (int(termcolor[c][3:5], 16) - self.g) ** 2 + (int(termcolor[c][5:], 16) - self.b) ** 2
      a = colorsys.rgb_to_hsv(float(int(termcolor[c][1:3], 16)), float(int(termcolor[c][3:5], 16)), float(int(termcolor[c][5:], 16)))
      b = colorsys.rgb_to_hsv(float(self.r), float(self.g), float(self.b))
      d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + ((a[2] - b[2]) / 255.0) ** 2
      if d < smallest_distance:
        smallest_distance = d
        best_match = c
    return best_match

class Agroup:
  def __init__(self, attrib, guifg, guibg):
    self.attrib = attrib.lower().split(',')

    guifg = guifg.lower()
    guibg = guibg.lower()

    if re_hexcolor.match(guifg):
      self.fg = color(int(guifg[1:3], 16), int(guifg[3:5], 16), int(guifg[5:], 16))
    elif guifg in ('fg', 'bg', 'none', 'nothing'):
      self.fg = guifg
    else:
      try:
        self.fg = name2hex[guifg]
      except KeyError:
        print rgbfile, _('中没有这种颜色名称：'), guifg
        self.fg = color(255, 255, 255)

    if re_hexcolor.match(guibg):
      self.bg = color(int(guibg[1:3], 16), int(guibg[3:5], 16), int(guibg[5:], 16))
    elif guibg in ('fg', 'bg', 'none'):
      self.bg = guibg
    else:
      try:
        self.bg = name2hex[guibg]
      except KeyError:
        print rgbfile, _('中没有这种颜色名称：'), guibg
        self.bg = color()

  def termToString(self):
    attrib = self.attrib
    for i in attrib[:]:
      if i == 'italic':
        attrib.remove(i)
    if len(attrib) == 0:
      attrib = 'NONE'
    else:
      attrib = ','.join(attrib)

    try:
      return 'ctermfg=' + str(self.fg.rgb2xterm()) + ' ctermbg=' + str(self.bg.rgb2xterm()) + ' cterm=' + attrib
    except AttributeError:
      if self.fg != 'nothing':
        if self.fg in ('fg', 'none'):
          self.fg = groups['Normal'].fg
        elif self.fg == 'bg':
          self.fg = groups['Normal'].bg
        if self.bg in ('bg', 'none'):
          self.bg = groups['Normal'].bg
        elif self.bg == 'fg':
          self.bg = groups['Normal'].fg
        return 'ctermfg=' + str(self.fg.rgb2xterm()) + ' ctermbg=' + str(self.bg.rgb2xterm()) + ' cterm=' + attrib
      else:
        if self.bg in ('bg', 'none'):
          self.bg = groups['Normal'].bg
        elif self.bg == 'fg':
          self.bg = groups['Normal'].fg
        return 'ctermbg=' + str(self.bg.rgb2xterm()) + ' cterm=' + attrib

def read(file):
  '''读取配色信息'''
  f = open(file)
  re_guifg = re.compile('(?<=guifg=)(#[0-9a-fA-F]{6}|\w+|\'[^\']+\')')
  re_guibg = re.compile('(?<=guibg=)(#[0-9a-fA-F]{6}|\w+|\'[^\']+\')')
  re_guiattrib = re.compile('(?<=gui=)[a-zA-Z,]+')
  l = f.readline()

  while l:
    if l.strip().find('"') == 0: #注释
      l = f.readline()
      continue
    if re_hiline.match(l):
      try:
        name = re_name.search(l).group(0)
      except AttributeError:
        l = f.readline()
        continue
      try:
        attrib = re_guiattrib.search(l).group(0)
      except AttributeError:
        attrib = 'NONE'
      try:
        guifg = re_guifg.search(l).group(0)
      except AttributeError:
        guifg = 'nothing'
      try:
        guibg = re_guibg.search(l).group(0)
      except AttributeError:
        # 像 Ignore 组，没有前景和背景颜色，但是显示时却前景色竟然是白的
        guibg = 'bg'
      groups[name] = Agroup(attrib, guifg, guibg)

    l = f.readline()

  f.close()

def write(file, src):
  '''写新文件'''
  f = open(file, 'w')
  f.write('" ' + by + '\n')
  for l in open(src):
    if re_hiline.match(l):
      try:
        name = re_name.search(l).group(0)
      except AttributeError:
        f.write(l)
        continue
      a = l[:-1]
      a += ' ' + groups[name].termToString() + '\n'
      f.write(a)
    else:
      f.write(l)

  f.close()

def convert(src, tgt):
  loadRgb(rgbfile)
  read(src)
  write(tgt, src)

def loadRgb(rgbfile):
  rgbtxt = re.compile('^(\d+)\s+(\d+)\s+(\d+)\s+([\w\s]+)$')
  try:
    f = open(rgbfile)
    l = f.readline().strip()
    while l:
      a = rgbtxt.match(l)
      try:
        name2hex[a.group(4).lower()] = color(int(a.group(1)), int(a.group(2)), int(a.group(3)))
      except AttributeError:
        pass
      l = f.readline().strip()
    f.close()
  except IOError:
    print _('抱歉，打开文件'), rgbfile, _('失败！')

if __name__ == '__main__':
  if len(sys.argv) == 3:
    try:
      loadRgb(rgbfile)
      convert(sys.argv[1], sys.argv[2])
    except IOError:
      print _('打开文件指定文件失败！')
  else:
    print _('用法：\n\tgui2term.py 原文件 新文件')

