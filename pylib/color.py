# vim:fileencoding=utf-8

from math import sqrt, degrees, atan2, fabs, cos, radians, sin, exp

def hex2tuple(c):
  return tuple(int(x, 16)/255.0 for x in (c[1:3], c[3:5], c[5:7]))

def best_match(colortuple, mapping):
  best_match = None
  smallest_distance = 10000000

  dest = rgb2lab(colortuple)
  for c, v in mapping.items():
    d = delta_e_cie2000(dest, c)

    if d < smallest_distance:
      smallest_distance = d
      best_match = (c, v)

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
