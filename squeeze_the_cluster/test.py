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

print("primes between 0-10000: {}".format(count_primes((0,10000))))

# message parsing
class Test_Msg:

    def __init__(self):
        self.payload = None

my_request = ':'.join(['0','1',Msg.request])
my_task = ':'.join(['0','1',Msg.task,'111','0','1000'])
my_assigned_task = ':'.join(['0','1',Msg.task,'111','0','1000','1'])
my_result = ':'.join(['0','1',Msg.result,'111','0','1000','1','169'])
my_stop = ':'.join(['0','1',Msg.stop])

my_msg = Test_Msg

for test_payload in [my_request, my_task, my_assigned_task, my_result, my_stop]:
    my_msg.payload = test_payload
    src_uid, dst_uid, msg_type, payload = parse_msg(my_msg)
    print("src={}, dst={}, msg_type={}, payload={}".format(src_uid, dst_uid, msg_type, payload))
    if msg_type == Msg.task:
        test_task = Task.from_payload(payload)
        print("Created task: {}".format(test_task))
    elif msg_type == Msg.result:
        test_task = Task.from_payload(payload)
        print("Created result: {}".format(test_task))


# supervisor tests
my_sup = Supervisor(0, 10000, 1000)
my_worker = Worker(1)

print("created {} tasks".format(my_sup.bag.qsize()))

while not my_sup.bag.empty():
    task = my_sup.bag.get()
    print(task)

my_sup.make_work(0, 100000, 1000)

# test reaping uid
task1 = my_sup.bag.get()
task2 = my_sup.bag.get()

task1.worker_uid.append(1)
task2.worker_uid.append(1)
task2.worker_uid.append(2)
my_sup.pending[task1.uid] = task1
my_sup.pending[task2.uid] = task2
print("before reaping uid 1")
for task in my_sup.pending.values():
    print task
my_sup.reap_uid(1)
print("after reaping uid 1")
for task in my_sup.pending.values():
    print task

