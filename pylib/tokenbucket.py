import time

class TokenBucket:
  def __init__(self, rate, cap):
    self.rate = rate
    self.cap = cap
    self.tokens = cap
    self.ts = time.time()

  def consume_token(self):
    t = time.time()
    self.tokens += (t - self.ts) * self.rate
    self.tokens = min(self.tokens, self.cap)
    self.ts = t

    if self.tokens < 1:
      return False
    else:
      self.tokens -= 1
      return True

