'''
关于字符集的相关数据和函数

2011年3月10日
'''

import myutils

全角字符 = r'！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～￠￡￢￣￤￥'
半角字符 = r'''!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~¢£¬¯¦¥'''
数字 = '零一二三四五六七八九个十百千万'

def zhnum(num):
  '''阿拉伯数字转中文'''
  import re
  if not isinstance(num, int) and not isinstance(num, float):
    raise TypeError('目前只能处理整数和小数')
  if num >= 100000:
    raise ValueError('目前只能处理到十万以内')
  sign = num < 0 and -1 or 1
  isfloat = isinstance(num, float) and True or False
  N = abs(int(num))
  ans = []
  for k, n in enumerate(str(N)[::-1]):
    a = 数字[int(n)] + 数字[10+k]
    if a == '零十' or a == '零百':
      a = '零'
    elif a[0] == '零':
      continue
    ans.append(a)
  ret = ''.join(ans[::-1])
  ret = ret.rstrip('零')
  ret = re.sub(r'零+', '零', ret)
  if ret.endswith('个'):
    ret = ret[:-1]
  if not ret:
    ret = '零'

  if sign == -1:
    ret = '负' + ret

  if isfloat:
    ret += '点'
    l = []
    left = abs(num) - N
    left = str(left)[2:]
    for n in left:
      l.append(数字[int(n)])
    ret += ''.join(l)
  return ret

def 全角转半角(字符串, 仅字母数字=True):
  if not isinstance(字符串, str):
    raise TypeError('参数类型不匹配：需要 str 类型参数')

  返回值 = ''
  for 字符 in 字符串:
    位置 = 全角字符.find(字符)
    if 位置 == -1 or 仅字母数字 and not 半角字符[位置].isalnum():
      返回值 += 字符
    else:
      返回值 += 半角字符[位置]

  return 返回值

qjzf = 全角字符
bjzf = 半角字符
qjzbj = 全角转半角

# 0 表示未知
星座 = ['', '水瓶座', '双鱼座', '白羊座', '金牛座', '双子座',
    '巨蟹座', '狮子座', '处女座', '天秤座', '天蝎座', '人马座', '山羊宫']
Constellation = 星座

生肖 = '鼠牛虎兔龙蛇马羊猴鸡狗猪'

def 宽度_py(字符串, ambiwidth=2):
  '''ambiwidth: 宽度不定的字符算几个，取值为 1, 2'''
  if ambiwidth == 2:
    双宽度 = ('W', 'A')
  elif ambiwidth == 1:
    双宽度 = ('W',)
  else:
    raise ValueError('ambiwidth 取值为 1 或者 2')

  import unicodedata
  count = 0
  for i in 字符串:
    if unicodedata.east_asian_width(i) in 双宽度:
      count += 2
      continue
    count += 1
  return count

try:
  from ctypes import *
  _w = myutils.loadso('_wchar.so')
  _w.width.argtypes = (c_wchar_p,)
  _w.width.restype = c_size_t
  def 宽度(字符串, ambiwidth=1):
    '''
    ambiwidth 被忽略

    这样比纯 Python 的 `宽度_py' 速度要快一倍以上
    '''
    return _w.width(字符串)
except ImportError:
  宽度 = 宽度_py

width = 宽度

def _CJK_align(字符串, 对齐宽度, 方向='左', 填充=' '):
  '''对齐字符串，考虑字符宽度，不检测是否是ASCII字符串'''
  if len(填充) != 1:
    raise ValueError('填充字符只能是一个字符')

  if 方向 == '右':
    return 填充 * round(((对齐宽度 - 宽度(字符串)) / 宽度(填充))) + 字符串
  elif 方向 == '左':
    return 字符串 + 填充 * round(((对齐宽度 - 宽度(字符串)) / 宽度(填充)))
  else:
    raise ValueError("`方向' 可选为 '左' 或者 '右'")

def CJK_align(字符串, 对齐宽度, 方向='左', 填充=' '):
  '''对齐字符串，考虑字符宽度'''
  if isascii(字符串):
    if 方向 == '右':
      return 字符串.rjust(对齐宽度, 填充)
    elif 方向 == '左':
      return 字符串.ljust(对齐宽度, 填充)
    else:
      raise ValueError("`方向' 可选为 '左' 或者 '右'")
  else:
    return _CJK_align(字符串, 对齐宽度, 方向, 填充)

def isascii(string):
  for i in string:
    if ord(i) > 255:
      return False
  return True

# vim:tw=78:et:sts=2:fdm=expr:fde=getline(v\:lnum)=~'\\v^\\S.*\:(\\s*#.*)?$'?'>1'\:1
