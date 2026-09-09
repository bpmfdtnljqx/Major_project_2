# P1002 最大公约数 — Python 样例（可直接提交，AC）
import sys

a, b = map(int, sys.stdin.read().split())
while b:
    a, b = b, a % b
print(a)
