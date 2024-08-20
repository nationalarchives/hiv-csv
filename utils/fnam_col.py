#!/usr/bin/env python3

def n2a(n): #This function by Giancarlo Sportelli, https://stackoverflow.com/a/37604105
  d, m = divmod(n, 26)
  return '' if n < 0 else n2a(d - 1) + chr(m + 65)

def f2c(field_name):
  return n2a(int(field_name[1:]) - 1)

def c2i(col_name):
  def a2n(a, depth = 0):
    if len(a) == 0: return 0
    return (ord(a[-1]) - 64) * 26 ** depth + a2n(a[0:-1], depth + 1)
  return a2n(col_name.upper())

def c2f(col_name):
  return f'V{c2i(col_name)}'

if __name__ == '__main__':
  import re
  import sys
  for x in sys.argv[1:]:
    if re.fullmatch('[Vv]\d+', x):
      print(f'{x}: {f2c(x)}')
    elif re.fullmatch('[A-Za-z]+', x):
      print(f'{x}: {c2f(x)}')
    else:
      print(f'Do not know how to interpret "{x}"', file = sys.stderr)
      print('''
  This program converts field names to spreadsheet col references (V10 -> J) OR
                        spreadsheet col references to field names (J -> V10)''')
