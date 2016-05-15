"""
Put any module tests for squeeze.py here
"""

from squeeze import *


# test prime counting
assert list(chunks(0,1000,1000//4)) == [(0,250), (251,500), (501,750), (751,1000)]
assert count_primes((0,0)) == 0
assert count_primes((0,1)) == 1
assert count_primes((0,2)) == 2
assert count_primes((0,1000)) == 169
assert mp_count_primes(0,1000) == 169


# message parsing
class Test_Msg:

    def __init__(self):
        self.payload = None

my_request = ':'.join(['0','1',Msg.request])
my_task = ':'.join(['0','1',Msg.task,'111','0','1000','1'])
my_result = ':'.join(['0','1',Msg.result,'111','0','1000','1','169'])
my_stop = ':'.join(['0','1',Msg.stop])

my_msg = Test_Msg

for test_payload in [my_request, my_task, my_result, my_stop]:
    my_msg.payload = test_payload
    src_uid, dst_uid, msg_type, payload = parse_msg(my_msg)
    print("src={}, dst={}, msg_type={}, payload={}".format(src_uid, dst_uid, msg_type, payload))

test_task = Task.from_payload(my_task)
print(test_task)
test_result = Task.from_payload(my_result)
print(test_result)