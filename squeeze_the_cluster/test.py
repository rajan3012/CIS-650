"""
Put any module tests for squeeze.py here
"""

from squeeze import *

my_worker = Worker(101)

count1 = count_primes( (0, 1000))
count2 = mp_count_primes(0, 1000)
print count1, count2