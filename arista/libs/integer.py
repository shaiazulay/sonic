
def iterBits(n):
   while n:
      yield n & 0x1
      n >>= 1
