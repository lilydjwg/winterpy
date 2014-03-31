'''
benchmark:

In [2]: %timeit colorfinder.hex2term_accurate('#434519')
100 loops, best of 3: 5.06 ms per loop

In [3]: %timeit colorfinder.hex2term_quick('#434519')
100000 loops, best of 3: 12.2 µs per loop
'''

from math import sqrt, degrees, atan2, fabs, cos, radians, sin, exp
from functools import lru_cache

def parsehex_float(c):
  return tuple(int(x, 16)/255.0 for x in (c[1:3], c[3:5], c[5:7]))

def parsehex_int(c):
  return tuple(int(x, 16) for x in (c[1:3], c[3:5], c[5:7]))

def best_match(colortuple, mapping):
  best_match = None
  smallest_distance = 10000000

  dest = rgb2lab(colortuple)
  for v, c in mapping.items():
    d = delta_e_cie2000(dest, c)

    if d < smallest_distance:
      smallest_distance = d
      best_match = (v, c)

  return best_match

def rgb2lab(colortuple):
  '''RGB to XYZ then to Lab'''
  return xyz2lab(rgb2xyz(colortuple))

def rgb2xyz(colortuple):
  '''RGB to XYZ'''
  # http://www.easyrgb.com/index.php?X=MATH&H=02#text2
  r, g, b = colortuple

  if r > 0.04045 :
    r = ((r + 0.055) / 1.055) ** 2.4
  else:
    r = r / 12.92
  if g > 0.04045 :
    g = ((g + 0.055) / 1.055) ** 2.4
  else:
    g = g / 12.92
  if b > 0.04045 :
    b = ((b + 0.055) / 1.055) ** 2.4
  else:
    b = b / 12.92

  r = r * 100
  g = g * 100
  b = b * 100

  X = r * 0.4124 + g * 0.3576 + b * 0.1805
  Y = r * 0.2126 + g * 0.7152 + b * 0.0722
  Z = r * 0.0193 + g * 0.1192 + b * 0.9505
  return X, Y, Z

def xyz2lab(xyz):
  '''XYZ to Lab'''
  # http://www.easyrgb.com/index.php?X=MATH&H=07#text7
  X, Y, Z = xyz

  X /=  95.047
  Y /= 100.000
  Z /= 108.883

  if (X > 0.008856):
    X = X ** (1/3)
  else:
    X = (7.787 * X) + (16 / 116)
  if (Y > 0.008856):
    Y = Y ** (1/3)
  else:
    Y = (7.787 * Y) + (16 / 116)
  if (Z > 0.008856):
    Z = Z ** (1/3)
  else:
    Z = (7.787 * Z) + (16 / 116)

  L = (116 * Y) - 16
  a = 500 * (X - Y)
  b = 200 * (Y - Z)

  return L, a, b

def delta_e_cie2000(color1, color2):
  """
  Calculates the Delta E (CIE2000) of two colors. Colors are given in Lab tuples.

  Stolen from colormath.color_objects
  """
  Kl = Kc = Kh = 1
  L1, a1, b1 = color1
  L2, a2, b2 = color2

  avg_Lp = (L1 + L2) / 2.0
  C1 = sqrt(pow(a1, 2) + pow(b1, 2))
  C2 = sqrt(pow(a2, 2) + pow(b2, 2))
  avg_C1_C2 = (C1 + C2) / 2.0

  G = 0.5 * (1 - sqrt(pow(avg_C1_C2 , 7.0) / (pow(avg_C1_C2, 7.0) + pow(25.0, 7.0))))

  a1p = (1.0 + G) * a1
  a2p = (1.0 + G) * a2
  C1p = sqrt(pow(a1p, 2) + pow(b1, 2))
  C2p = sqrt(pow(a2p, 2) + pow(b2, 2))
  avg_C1p_C2p =(C1p + C2p) / 2.0

  if degrees(atan2(b1,a1p)) >= 0:
    h1p = degrees(atan2(b1,a1p))
  else:
    h1p = degrees(atan2(b1,a1p)) + 360

  if degrees(atan2(b2,a2p)) >= 0:
    h2p = degrees(atan2(b2,a2p))
  else:
    h2p = degrees(atan2(b2,a2p)) + 360

  if fabs(h1p - h2p) > 180:
    avg_Hp = (h1p + h2p + 360) / 2.0
  else:
    avg_Hp = (h1p + h2p) / 2.0

  T = 1 - 0.17 * cos(radians(avg_Hp - 30)) + 0.24 * cos(radians(2 * avg_Hp)) + 0.32 * cos(radians(3 * avg_Hp + 6)) - 0.2  * cos(radians(4 * avg_Hp - 63))

  diff_h2p_h1p = h2p - h1p
  if fabs(diff_h2p_h1p) <= 180:
    delta_hp = diff_h2p_h1p
  elif (fabs(diff_h2p_h1p) > 180) and (h2p <= h1p):
    delta_hp = diff_h2p_h1p + 360
  else:
    delta_hp = diff_h2p_h1p - 360

  delta_Lp = L2 - L1
  delta_Cp = C2p - C1p
  delta_Hp = 2 * sqrt(C2p * C1p) * sin(radians(delta_hp) / 2.0)

  S_L = 1 + ((0.015 * pow(avg_Lp - 50, 2)) / sqrt(20 + pow(avg_Lp - 50, 2.0)))
  S_C = 1 + 0.045 * avg_C1p_C2p
  S_H = 1 + 0.015 * avg_C1p_C2p * T

  delta_ro = 30 * exp(-(pow(((avg_Hp - 275) / 25), 2.0)))
  R_C = sqrt((pow(avg_C1p_C2p, 7.0)) / (pow(avg_C1p_C2p, 7.0) + pow(25.0, 7.0)));
  R_T = -2 * R_C * sin(2 * radians(delta_ro))

  delta_E = sqrt(pow(delta_Lp /(S_L * Kl), 2) + pow(delta_Cp /(S_C * Kc), 2) + pow(delta_Hp /(S_H * Kh), 2) + R_T * (delta_Cp /(S_C * Kc)) * (delta_Hp / (S_H * Kh)))

  return delta_E

def prepare_map(hexrgbmap):
  return {
    k: rgb2lab(parsehex_float(v))
    for k, v in termcolors.items()
  }

@lru_cache(300)
def hex2term_accurate(color):
  global _termcolors_map
  if _termcolors_map is None:
    _termcolors_map = prepare_map(termcolors)

  return best_match(parsehex_float(color), _termcolors_map)[0]

def _hex2term_quick(red, green, blue):
  # from ruby-paint
  gray_possible = True
  sep = 42.5
  gray = False

  while gray_possible:
    if red < sep or green < sep or blue < sep:
      gray = red < sep and green < sep and blue < sep
      gray_possible = False
    sep += 42.5

  if gray:
    return 232 + (red + green + blue) // 33
  else:
    return 16 + sum(6 * x // 256 * 6 ** i
                    for i, x in enumerate((blue, green, red)))

def hex2term_quick(color):
  return _hex2term_quick(*parsehex_int(color))

def htmltest():
  from random import randrange

  print('''\
<!DOCTYPE html>
<meta charset="utf-8" />
<title>Terminal Color Approximation Test</title>
<table>
  <thead>
    <tr><th>Accurate</th><th>Orignal</th><th>Quick</th><th>Same?</th></tr>
  </thead>
  <tbody>''')
  for i in range(100):
    r = randrange(256)
    g = randrange(256)
    b = randrange(256)
    c = '#%02x%02x%02x' % (r, g, b)
    c_a = termcolors[hex2term_accurate(c)]
    c_q = termcolors[hex2term_quick(c)]
    same = c_a == c_q and '\N{HEAVY CHECK MARK}' or '\N{HEAVY BALLOT X}'
    print('''\
    <tr>
      <td style="background-color: {c_a}">{c_a}</td>
      <td style="background-color: {c}">{c}</td>
      <td style="background-color: {c_q}">{c_q}</td>
      <td>{same}</td>
    </tr>'''.format(c=c, c_a=c_a, c_q=c_q, same=same))
  print('''\
  </tbody>
</table>''')

_termcolors_map = None

termcolors = {
  16: '#000000', 17: '#00005f', 18: '#000087',
  19: '#0000af', 20: '#0000d7', 21: '#0000ff',
  22: '#005f00', 23: '#005f5f', 24: '#005f87',
  25: '#005faf', 26: '#005fd7', 27: '#005fff',
  28: '#008700', 29: '#00875f', 30: '#008787',
  31: '#0087af', 32: '#0087d7', 33: '#0087ff',
  34: '#00af00', 35: '#00af5f', 36: '#00af87',
  37: '#00afaf', 38: '#00afd7', 39: '#00afff',
  40: '#00d700', 41: '#00d75f', 42: '#00d787',
  43: '#00d7af', 44: '#00d7d7', 45: '#00d7ff',
  46: '#00ff00', 47: '#00ff5f', 48: '#00ff87',
  49: '#00ffaf', 50: '#00ffd7', 51: '#00ffff',
  52: '#5f0000', 53: '#5f005f', 54: '#5f0087',
  55: '#5f00af', 56: '#5f00d7', 57: '#5f00ff',
  58: '#5f5f00', 59: '#5f5f5f', 60: '#5f5f87',
  61: '#5f5faf', 62: '#5f5fd7', 63: '#5f5fff',
  64: '#5f8700', 65: '#5f875f', 66: '#5f8787',
  67: '#5f87af', 68: '#5f87d7', 69: '#5f87ff',
  70: '#5faf00', 71: '#5faf5f', 72: '#5faf87',
  73: '#5fafaf', 74: '#5fafd7', 75: '#5fafff',
  76: '#5fd700', 77: '#5fd75f', 78: '#5fd787',
  79: '#5fd7af', 80: '#5fd7d7', 81: '#5fd7ff',
  82: '#5fff00', 83: '#5fff5f', 84: '#5fff87',
  85: '#5fffaf', 86: '#5fffd7', 87: '#5fffff',
  88: '#870000', 89: '#87005f', 90: '#870087',
  91: '#8700af', 92: '#8700d7', 93: '#8700ff',
  94: '#875f00', 95: '#875f5f', 96: '#875f87',
  97: '#875faf', 98: '#875fd7', 99: '#875fff',
  100: '#878700', 101: '#87875f', 102: '#878787',
  103: '#8787af', 104: '#8787d7', 105: '#8787ff',
  106: '#87af00', 107: '#87af5f', 108: '#87af87',
  109: '#87afaf', 110: '#87afd7', 111: '#87afff',
  112: '#87d700', 113: '#87d75f', 114: '#87d787',
  115: '#87d7af', 116: '#87d7d7', 117: '#87d7ff',
  118: '#87ff00', 119: '#87ff5f', 120: '#87ff87',
  121: '#87ffaf', 122: '#87ffd7', 123: '#87ffff',
  124: '#af0000', 125: '#af005f', 126: '#af0087',
  127: '#af00af', 128: '#af00d7', 129: '#af00ff',
  130: '#af5f00', 131: '#af5f5f', 132: '#af5f87',
  133: '#af5faf', 134: '#af5fd7', 135: '#af5fff',
  136: '#af8700', 137: '#af875f', 138: '#af8787',
  139: '#af87af', 140: '#af87d7', 141: '#af87ff',
  142: '#afaf00', 143: '#afaf5f', 144: '#afaf87',
  145: '#afafaf', 146: '#afafd7', 147: '#afafff',
  148: '#afd700', 149: '#afd75f', 150: '#afd787',
  151: '#afd7af', 152: '#afd7d7', 153: '#afd7ff',
  154: '#afff00', 155: '#afff5f', 156: '#afff87',
  157: '#afffaf', 158: '#afffd7', 159: '#afffff',
  160: '#d70000', 161: '#d7005f', 162: '#d70087',
  163: '#d700af', 164: '#d700d7', 165: '#d700ff',
  166: '#d75f00', 167: '#d75f5f', 168: '#d75f87',
  169: '#d75faf', 170: '#d75fd7', 171: '#d75fff',
  172: '#d78700', 173: '#d7875f', 174: '#d78787',
  175: '#d787af', 176: '#d787d7', 177: '#d787ff',
  178: '#d7af00', 179: '#d7af5f', 180: '#d7af87',
  181: '#d7afaf', 182: '#d7afd7', 183: '#d7afff',
  184: '#d7d700', 185: '#d7d75f', 186: '#d7d787',
  187: '#d7d7af', 188: '#d7d7d7', 189: '#d7d7ff',
  190: '#d7ff00', 191: '#d7ff5f', 192: '#d7ff87',
  193: '#d7ffaf', 194: '#d7ffd7', 195: '#d7ffff',
  196: '#ff0000', 197: '#ff005f', 198: '#ff0087',
  199: '#ff00af', 200: '#ff00d7', 201: '#ff00ff',
  202: '#ff5f00', 203: '#ff5f5f', 204: '#ff5f87',
  205: '#ff5faf', 206: '#ff5fd7', 207: '#ff5fff',
  208: '#ff8700', 209: '#ff875f', 210: '#ff8787',
  211: '#ff87af', 212: '#ff87d7', 213: '#ff87ff',
  214: '#ffaf00', 215: '#ffaf5f', 216: '#ffaf87',
  217: '#ffafaf', 218: '#ffafd7', 219: '#ffafff',
  220: '#ffd700', 221: '#ffd75f', 222: '#ffd787',
  223: '#ffd7af', 224: '#ffd7d7', 225: '#ffd7ff',
  226: '#ffff00', 227: '#ffff5f', 228: '#ffff87',
  229: '#ffffaf', 230: '#ffffd7', 231: '#ffffff',
  232: '#080808', 233: '#121212', 234: '#1c1c1c',
  235: '#262626', 236: '#303030', 237: '#3a3a3a',
  238: '#444444', 239: '#4e4e4e', 240: '#585858',
  241: '#626262', 242: '#6c6c6c', 243: '#767676',
  244: '#808080', 245: '#8a8a8a', 246: '#949494',
  247: '#9e9e9e', 248: '#a8a8a8', 249: '#b2b2b2',
  250: '#bcbcbc', 251: '#c6c6c6', 252: '#d0d0d0',
  253: '#dadada', 254: '#e4e4e4', 255: '#eeeeee',
}

if __name__ == '__main__':
  htmltest()
