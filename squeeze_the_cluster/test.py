"""
Put any module tests for squeeze.py here
"""

from squeeze import *

my_worker = Worker(101)

count1 = my_worker.mp_count_primes(0, 100000)
print count1