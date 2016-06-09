"""
CIS 650 
SPRING 2016
Rickie Kerndt <rkerndt@cs.uoregon.edu>
"""
from ast import literal_eval
from ricart_agrawala import *
from pi_stuff import *

class Task:
    def __init__(self, uid, units = 0, worker_uid = None, result = None):
        self.uid = uid
        self.units = units
        self.worker_uid = []
        if worker_uid is not None:
            self.worker_uid.append(worker_uid)
        self.result = result

    @classmethod
    def from_payload(cls, payload):
        # fields is a list of arguments
        fields = payload.split(':')

        # two should always be there
        uid = int(fields[0])
        units = int(fields[1])

        worker_uid = None
        if len(fields) >= 3:
            worker_uid = literal_eval(fields[2])[0]

        result = None
        if (len(fields) == 4) and (fields[3] != "None"):
            result = int(fields[3])

        return cls(uid, units, worker_uid, result)

    def __str__(self):
        return ':'.join([str(self.uid), str(self.units), str(self.worker_uid), str(self.result)])


class Worker(Ricart_Agrawala):

    def __init__(self, uid,  neighbors):

        Ricart_Agrawala.__init__(self, uid, Role.worker, neighbors)
        self.request_sent = False
        self.work_topic = 'hauler'
        self.my_task = None
        self.topics.append(self.work_topic)

    def process_incoming(self, msg):
        src_uid, dst_uid, msg_type, payload = parse_payload(msg)

        if dst_uid != self.uid:
            return
        if msg_type == Msg.task:
            self.process_task(payload)
        elif msg_type == Msg.stop:
            pass
        else:
            Ricart_Agrawala.process_incoming(self, msg)

    def process_task(self, payload):
        self.my_task = Task.from_payload(payload)
        print('{} received task {} to haul {} units'.format(self.uid, self.my_task.uid, self.my_task.units))
        print('{} is requesting crane'.format(self.uid))
        self.get_resource(self.load_ringo)

    def send_result(self, task):
        payload = str(task)
        msg = construct_payload(self.uid, '0', Msg.result, payload)
        self.publish(self.work_topic, msg)

    def request_task(self):
        msg = construct_payload(self.uid, '0', Msg.task_request)
        self.publish(self.work_topic, msg)
        self.request_sent = True

    def load_ringo(self):
        """
        critical section for ringo hauling
        """
        print('{} has permission to operate crane, hold button while in use')

        while not is_button_on():
            pass
        print('{} is operating crane')
        while is_button_on():
            pass
        print('{} has finished loading')


    def haul_load(self):
        """
        non-critical section of ringo hauling
        """
        signal_ringo(RINGO_GO)
        print('{} is loaded and hauling'.format(self.uid))

        while not receive_ringo(RINGO_DONE):
            interruptable_sleep(2)

        self.my_task.result = randint(0, self.my_task.units)
        self.send_result(self.my_task)
        self.my_task = None
        self.request_sent = False

    def duties(self):
        """
        main worker loop, checks to see whether a task is needed every 10 seconds
        """
        while not self.abort:

            if not self.request_sent:
                self.request_task()

            # evaluates true only after have received a task and permission to use crane
            # (critical resource)
            if self.count == self.need:
                self.start_critical()
                self.haul_load()

            interruptable_sleep(10)

class Supervisor(Ricart_Agrawala):

    def __init__(self, uid, neighbors):
        Ricart_Agrawala.__init__(self, uid, Role.supervisor, neighbors)
        self.work_topic = 'hauler'
        self.bag = Queue()
        self.pending = {}
        self.results = {}
        self.done = False
        self.output_done = False

        self.topics.append(self.work_topic)

        # fill the bag
        self.make_work()

    def make_work(self, num=10):
        for uid, units in enumerate(range(num)):
            more_work = Task(uid, randint(100,200))
            self.bag.put(more_work)

    def reap(self, uid, role):
        # put any pending tasks assigned only to the dead uid back in the bag
        for task in self.pending.values():
            if uid in task.worker_uid:
                task.worker_uid.remove(uid)
            if len(task.worker_uid) == 0:
                del(self.pending[task.uid])
                self.bag.put(task)
        Ricart_Agrawala.reap(self, uid, role)

    def process_request(self, uid):
        print("Processing request from {}".format(uid))
        send_task = None
        try:
            send_task = self.bag.get_nowait()
        except Empty:
            # I would prefer that such an operation would return None rather than raise an exception
            pass
        if send_task is not None:
            send_task.worker_uid.append(uid)
            self.pending[send_task.uid] = send_task
            new_msg = construct_payload(self.uid, uid, Msg.task, str(send_task))
        elif len(self.pending) > 0:
            # send out a pending task assigned to fewest workers
            send_task = min(self.pending.values(), key=lambda v: len(v.worker_uid))
            send_task.worker_uid.append(uid)
            new_msg = construct_payload(self.uid, uid, Msg.task, str(send_task))
        else:
            # send out a stop message
            new_msg = construct_payload(self.uid, uid, Msg.stop)
        self.publish(self.work_topic, new_msg)

    def process_result(self, result, uid):
        if result.uid not in self.results:
            print("Received results for task {} from {} with count={}".format(result.uid, uid, result.result))
            self.results[result.uid] = result
        if result.uid in self.pending:
            del(self.pending[result.uid])
            if (self.bag.qsize() == 0) and (len(self.pending) == 0):
                self.done = True

    def process_incoming(self, msg):
        src_uid, dst_uid, msg_type, payload = parse_payload(msg)
        if dst_uid != self.uid:
            return
        if msg_type == Msg.task_request:
            self.process_request(src_uid)
        elif msg_type == Msg.result:
            self.process_result(Task.from_payload(payload), src_uid)
        else:
            Ricart_Agrawala.process_incoming(self, msg)

    def duties(self):
        """
        main loop, since all processes are message driven, check for abort every 10
        seconds
        """

        while not self.abort:
            interruptable_sleep(10)



'''
---------------------------------------------------------------------
    MAIN
---------------------------------------------------------------------
'''


def main():
    """
    Main method takes command line arguments initialize and call duties
    UID zero is always the supervisor
    """
    optimization = False
    lazy = False

    if len(sys.argv) < 3:
        print 'ERROR\nusage: ringo_hauler <int: i> <int: neighbor1> ... [<int: neighborN>]'
        sys.exit()

    try:
        my_uid = int(sys.argv[1])
        neighbors = []
        for arg in sys.argv[2:]:
            neighbors.append(int(arg))
    except ValueError:
        print 'ERROR\nusage: ringo_hauler.py <int: i> <int: neighbor1> ... <int: neighborN> [-O]'
        sys.exit()

    if my_uid == 0:
        me = Supervisor(my_uid, neighbors)
    else:
        me = Worker(my_uid, neighbors)

    try:
        me.register()
        # sleep for 10 seconds while everyone gets started
        interruptable_sleep(10)
        me.duties()
        me.client.disconnect()
        sys.exit()

    except KeyboardInterrupt:
        print "Interrupt received"
        me.disconnect()
    except RuntimeError:
        print "Runtime Error"
        me.disconnect()

if __name__ == "__main__":
    main()