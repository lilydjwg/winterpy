'''一些算法'''

def LevenshteinDistance(s, t):
  '''字符串相似度算法（Levenshtein Distance算法）
  
一个字符串可以通过增加一个字符，删除一个字符，替换一个字符得到另外一个
字符串，假设，我们把从字符串A转换成字符串B，前面3种操作所执行的最少
次数称为AB相似度

这算法是由俄国科学家Levenshtein提出的。
Step Description
1 Set n to be the length of s.
  Set m to be the length of t.
  If n = 0, return m and exit.
  If m = 0, return n and exit.
  Construct a matrix containing 0..m rows and 0..n columns.
2 Initialize the first row to 0..n.
  Initialize the first column to 0..m.
3 Examine each character of s (i from 1 to n).
4 Examine each character of t (j from 1 to m).
5 If s[i] equals t[j], the cost is 0.
  If s[i] doesn't equal t[j], the cost is 1.
6 Set cell d[i,j] of the matrix equal to the minimum of:
  a. The cell immediately above plus 1: d[i-1,j] + 1.
  b. The cell immediately to the left plus 1: d[i,j-1] + 1.
  c. The cell diagonally above and to the left plus the cost:
     d[i-1,j-1] + cost.
7 After the iteration steps (3, 4, 5, 6) are complete, the distance is
  found in cell d[n,m]. '''

  m, n = len(s), len(t)
  if not (m and n):
    return m or n

  # 构造矩阵
  matrix = [[0 for i in range(n+1)] for j in range(m+1)]
  matrix[0] = list(range(n+1))
  for i in range(m+1):
    matrix[i][0] = i

  for i in range(m):
    for j in range(n):
      cost = int(s[i] != t[j])
      # 因为 Python 的字符索引从 0 开始
      matrix[i+1][j+1] = min(
          matrix[i][j+1] + 1, # a.
          matrix[i+1][j] + 1, # b.
          matrix[i][j] + cost # c.
          )

  return matrix[m][n]

difference = LevenshteinDistance

def mprint(matrix, width=3):
  '''打印矩阵'''

  for i in matrix:
    for j in i:
      print('{0:>{1}}'.format(j, width), end='')
    print()

def primes(start, stop):
  '''生成质数'''
  if start > stop:
    start, stop = stop, start
  if start <= 1:
    start = 2
  if start == 2:
    yield 2
    start += 1

  while start <= stop:
    for i in range(3, int(start**0.5), 2):
      if start % i == 0:
        break
    else:
      yield start
    start += 2

def 分解质因数(num):
  if num < 2:
    raise ValueError('需要大于 1 的整数')

  factors = []
  for i in primes(2, num+1):
    while num % i == 0:
      num /= i
      factors.append(i)
  return factors

def nmin(s, howmany):
  '''选取 howmany 个最小项
  
来源于 Python2.6 的文档
(tutorial/stdlib2.html#tools-for-working-with-lists)'''

  from heapq import heapify, heappop
  heapify(s)        # rearrange the list into heap order
  # fetch the smallest entries
  return [heappop(s) for i in range(howmany)]

def between(seq, start, end):
  '''获取 seq 中 start 和 end 之间的项

seq 应当已经排序过，并且是递增的'''

  l = 二分搜索(seq, start)
  if l < 0:
    l = 0
  r = 二分搜索(seq, end)
  try:
    while end == seq[r]:
      r += 1
  except IndexError:
    pass
  return seq[l:r]

def 二分搜索(l, tgt, gt=None):
  '''查找 l 中不比 tgt 小的位置
  
l 应当已经排序过，并且是递增的
lt(tgt,l[i]) 当 tgt 比 l[i] 大时返回真
'''
  # tgt 在 l 中存在
  # if tgt in l:
    # return l.index(tgt)
  # 这样很耗时的

  left = 0
  right = len(l)-1
  middle = -1
  if not gt:
    # 放在这里，只需要判断一次
    while left <= right:
      middle = (left+right) // 2
      if not tgt > l[middle]:
        right = middle - 1
      else:
        left = middle + 1
    try:
      while tgt == l[middle] and middle >= 0:
        middle -= 1
    except IndexError:
      pass
  else:
    while left <= right:
      middle = (left+right) // 2
      if not gt(tgt, l[middle]):
        right = middle - 1
      else:
        left = middle + 1
    try:
      while not gt(tgt, l[middle]) and middle >= 0:
        middle -= 1
    except IndexError:
      pass
  return middle+1

def 球面坐标到直角坐标(r, alpha, beta):
  from math import cos, sin
  x = r * cos(beta) * cos(alpha)
  y = r * cos(beta) * sin(alpha)
  z = r * sin(beta)
  return (x, y, z)

def md5(string):
  '''求 string (UTF-8) 的 md5 (hex 表示)'''
  import hashlib
  m = hashlib.md5()
  m.update(string.encode('utf-8'))
  return m.hexdigest()

