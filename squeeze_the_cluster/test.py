"""
Put any module tests for squeeze.py here
"""

from squeeze import *

assert list(chunks(0,1000,1000//4)) == [(0,250), (251,500), (501,750), (751,1000)]
assert count_primes((0,0)) == 0
assert count_primes((0,1)) == 1
assert count_primes((0,2)) == 2
assert count_primes((0,1000)) == 169
assert mp_count_primes(0,1000) == 169
