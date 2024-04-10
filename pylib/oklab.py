from math import cbrt, pi, cos, sin, pow

def oklab_to_rgb(L, a, b):
  l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  s_ = L - 0.0894841775 * a - 1.2914855480 * b;
  l = l_ ** 3
  m = m_ ** 3
  s = s_ ** 3

  r = int(255 * gamma(+4.0767245293 * l - 3.3072168827 * m + 0.2307590544 * s))
  g = int(255 * gamma(-1.2681437731 * l + 2.6093323231 * m - 0.3411344290 * s))
  b = int(255 * gamma(-0.0041119885 * l - 0.7034763098 * m + 1.7068625689 * s))

  return r, g, b

def rgb_to_oklab(r, g, b):
  r = gamma_inv(r / 255)
  g = gamma_inv(g / 255)
  b = gamma_inv(b / 255)
  l = 0.4121656120 * r + 0.5362752080 * g + 0.0514575653 * b
  m = 0.2118591070 * r + 0.6807189584 * g + 0.1074065790 * b
  s = 0.0883097947 * r + 0.2818474174 * g + 0.6302613616 * b

  l_ = cbrt(l)
  m_ = cbrt(m)
  s_ = cbrt(s)

  L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
  a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
  b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

  return L, a, b

def oklch_to_rgb(L, C, h):
  h = 2 * pi * h
  a = C * cos(h)
  b = C * sin(h)
  return oklab_to_rgb(L, a, b)

def gamma(x):
  if x >= 0.0031308:
    return 1.055 * pow(x, 1 / 2.4) - 0.055
  else:
    return 12.92 * x

def gamma_inv(x):
  if x >= 0.04045:
    return pow((x + 0.055) / (1 + 0.055), 2.4)
  else:
    return x / 12.92
