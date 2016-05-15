"""
CIS 650 
SPRING 2016
usage: squeeze.py <UID> <field(0), gate(1), neighbor1(2) , neighbor2(3)>

> For python mosquitto client $ sudo pip install paho-mqtt
> Command line arg to check status of broker $ /etc/init.d/mosquitto status 
"""
import sys
from time import sleep
import paho.mqtt.client as mqtt
from Queue import Queue, Empty
from math import sqrt, ceil
from multiprocessing import Pool, cpu_count
from ast import literal_eval

class Role:
    supervisor  = 0
    worker   = 1

class Msg:
    request = '0'
    task    = '1'
    result  = '2'
    stop    = '3'
    dead    = '4'

class Task:
    def __init__(self, uid, lo, up, worker_uid = None, result = None):
        self.uid = uid
        self.lo = lo
        self.up = up
        self.worker_uid = []
        if worker_uid is not None:
            self.worker_uid.append(worker_uid)
        self.result = result

    @classmethod
    def from_payload(cls, fields):
        # fields is a list of arguments

        # three should always be there
        uid = int(fields[0])
        lo = int(fields[1])
        up = int(fields[2])

        worker_uid = None
        if len(fields) >= 4:
            worker_uid = literal_eval(fields[3])

        result = None
        if (len(fields) == 5) and (fields[4] != "None"):
            result = int(fields[4])

        return cls(uid, lo, up, worker_uid, result)

    def __str__(self):
        s = Msg.task
        if self.result is not None:
            s = Msg.result
        return ':'.join([s, str(self.uid), str(self.lo), str(self.up), str(self.worker_uid), str(self.result)])

class Fake_Message:
    def __init__(self,payload):
        self.payload = payload

#############################################
## MQTT settings
#############################################
class MQTT:
    def __init__(self, my_uid):
        self.uid = my_uid

        self.client = None
        self.broker = "white0"
        self.port = 1883

        # topics
        self.topic = 'LINDA'
        self.will_topic = 'will/'

        # quality of service
        self.qos = 2
        self.keepalive = 30

        # status attributes
        self.connected = False
        self.abort = False

        # queue of outgoing messages
        self.outgoing = Queue()
        self.pub_pending = False # waiting for a publish confirmation

        # queue of incoming messages
        self.incoming = Queue()

    def publish(self, msg):
        if self.pub_pending or not self.outgoing.empty():
            self.outgoing.put( (self.topic, msg) )  # this is a blocking put
        else: # if the queue is empty and nothing pending just go ahead and publish
            self.pub_pending = True
            print("Publishing {},{}".format(self.topic, msg))
            self.client.publish(self.topic, msg, self.qos)

    def check_publish_queue(self):
        if not self.pub_pending and not self.outgoing.empty():
            try:
                topic, payload = self.outgoing.get_nowait()
            except Empty:
                return # nothing to do
            self.pub_pending = True
            print("Publishing {},{}".format(topic, payload))
            self.client.publish(topic, payload, self.qos)


class Worker(MQTT):

    def __init__(self, my_uid):
        MQTT.__init__(self, my_uid)
        self.role = Role.worker
        self.request_sent = False

    def duties(self):
        # main loop for a worker
        while not self.abort:

            # check to see if any tasks have been received
            msg = None
            try:
                msg = self.incoming.get_nowait()
            except Empty:
                # don't see this as a good use of exceptions
                pass
            if msg is not None:
                src_uid, dst_uid, msg_type, payload = parse_msg(msg)
                if msg_type == Msg.task:
                    self.request_sent = False
                    my_task = Task.from_payload(payload)
                    my_task.result = mp_count_primes(my_task.lo, my_task.up)
                    payload = str(my_task)
                    msg = ':'.join([str(self.uid), '0', payload])
                    self.publish(msg)
                elif msg_type == Msg.stop:
                    self.abort = True

            self.check_publish_queue()

            if not self.request_sent:
                msg = ':'.join([str(self.uid), '0', Msg.request])
                self.publish(msg)
                self.request_sent = True

            self.client.loop()

class Supervisor(MQTT):

    def __init__(self, uid, upper, sub_range):
        MQTT.__init__(self, uid)
        self.role = Role.supervisor
        self.upper = upper
        self.range = sub_range
        self.bag = Queue()
        self.pending = {}
        self.results = {}
        self.done = False
        self.output_done = False

        # fill the bag
        self.make_work(0, upper, sub_range)

    def make_work(self, lower, upper, sub_range):
        for uid, bounds in enumerate(chunks(lower, upper, sub_range)):
            sub_lower, sub_upper = bounds
            more_work = Task(uid, sub_lower, sub_upper)
            self.bag.put(more_work)

    def reap_uid(self, uid):
        # put any pending tasks assigned only to the dead uid back in the bag
        for task in self.pending.values():
            if uid in task.worker_uid:
                task.worker_uid.remove(uid)
            if len(task.worker_uid) == 0:
                del(self.pending[task.uid])
                self.bag.put(task)

    def process_request(self, uid):
        print("Processing request from {}".format(uid))
        new_msg = None
        # send task from bag until it is empty
        send_task = None
        try:
            send_task = self.bag.get_nowait()
        except Empty:
            # I would prefer that such an operation would return None rather than raise an exception
            pass
        if send_task is not None:
            send_task.worker_uid.append(uid)
            self.pending[send_task.uid] = send_task
            new_msg = ':'.join(['0',str(uid),str(send_task)])
        elif len(self.pending) > 0:
            # send out a pending task assigned to fewest workers
            send_task = min(self.pending.values, key=lambda v: len(v.worker_uid))
            send_task.worker_uid.append(uid)
            new_msg = ':'.join(['0',str(uid),str(send_task)])
        else:
            # send out a stop message
            new_msg = ':'.join(['0',str(uid),Msg.stop])
        self.publish(new_msg)

    def process_result(self, result, uid):
        if result.uid not in self.results:
            print("Received results for task {} from {} with count={}".format(result.uid, uid, result.result))
            self.results[result.uid] = result
        if result.uid in self.pending:
            del(self.pending[result.uid])
            if (self.bag.qsize() == 0) and (len(self.pending) == 0):
                self.done = True

    def duties(self):
        # main loop for a supervisor

        while not self.abort:

            # check for and handle incoming request and result messages
            msg = None
            try:
                msg = self.incoming.get_nowait()
            except Empty:
                # don't see this as a good use of exceptions
                pass
            if msg is not None:
                src_uid, dst_uid, msg_type, payload = parse_msg(msg)
                print("Retrieved msg_type={} from queue with payload: {}".format(msg_type, payload))
                if msg_type == Msg.request:
                    self.process_request(src_uid)
                elif msg_type == Msg.result:
                    self.process_result(Task.from_payload(payload), src_uid)
                elif msg_type == Msg.dead:
                    self.reap_uid(src_uid)
                else:
                    print("Received unexpected message type{}".format(msg_type))

            if self.done and not self.output_done:
                # output the final tally
                total_primes = 0
                for result in self.results.values():
                    total_primes += result.result
                print()
                print("The final tally for primes between {} and {} is {}".format(0, self.upper, total_primes))
                print()
                self.output_done = True

            self.check_publish_queue()

            self.client.loop()


##############################################
## MQTT callbacks
##############################################

#Called when the broker responds to our connection request
def on_connect(client, userdata, flags, rc):
    if rc != 0:
        print("Connection failed. RC: " + str(rc))
    else:
        print("Connected successfully with result code RC: " + str(rc))
        userdata.connected = True

#Called when a published message has completed transmission to the broker
def on_publish(client, userdata, mid):
    print("Message ID "+str(mid)+ " successfully published")
    userdata.pub_pending = False


#Called when message received on will_topic
def on_will(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    # abort where the supervisor dies
    if "role: " + str(Role.supervisor) in msg.payload:
        userdata.abort = True
    elif userdata.role == Role.supervisor:
        # construct a 'dead' message and place into incoming queue
        fields = msg.payload.split(' ')
        dead_uid = fields[1]
        dead_msg = ':'.join([str(dead_uid), '0', Msg.dead])
        userdata.incoming.put(Fake_Message(dead_msg))

#Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    print('unfiltered message')

#Callback method for LINDA topic
def on_linda(client, userdata, msg):
    src_uid, dst_uid, msg_type, payload = parse_msg(msg)
    #print("Received msg id={}, type={}, src={}, dst={}, payload={}".format(msg.id, msg_type, src_uid, dst_uid, payload))
    print("Received type={}, src={}, dst={}, payload={}".format(msg_type, src_uid, dst_uid, payload))
    if dst_uid == userdata.uid:
        print("Placing message into incoming queue")
        userdata.incoming.put(msg)

#############################################
## Utility methods
#############################################
def parse_msg(msg):
    msg_list = msg.payload.split(':')
    src_uid = int(msg_list[0])
    dst_uid = int(msg_list[1])
    msg_type = msg_list[2]
    payload = None
    if len(msg_list) > 3:
        payload = msg_list[3:]
    return src_uid, dst_uid, msg_type, payload

def chunks(lo, up, sub_range):
    lo_sub = lo
    up_sub = lo
    while up_sub < up:
        up_sub = up_sub + sub_range
        if up_sub > up:
            up_sub = up
        yield lo_sub, up_sub
        lo_sub = up_sub + 1

def count_primes(bounds):

    lower_bound, upper_bound = bounds
    count = 0

    # handle some edge conditions
    if lower_bound > upper_bound:
        return 0
    if upper_bound <= 0:
        return 0
    if upper_bound == 1:
        return 1
    if upper_bound == 2:
        return 2

    if lower_bound < 3:
        count = 2
        lower_bound = 3

    for n in range(lower_bound, upper_bound + 1):
        upper = int(ceil(sqrt(n)))
        is_prime = True
        for i in range(2, upper + 1):
            if n % i == 0:
                is_prime = False
                break
        if is_prime:
            count += 1

    return count

def mp_count_primes(lower_bound, upper_bound):
    pool = Pool()
    range = (upper_bound - lower_bound) // cpu_count()
    counts = pool.map(count_primes, chunks(lower_bound, upper_bound, range))
    count = reduce(lambda a, b: a+b, counts)
    return count



#############################################
## Main method takes command line arguments initialize and call duties
#############################################

def main():


    if len(sys.argv) < 3:
        print 'ERROR\nusage: squeeze.py <int: UID> <int: role>'
        sys.exit()

    try:
        my_uid = int(sys.argv[1])
        my_role = int(sys.argv[2])
    except ValueError:
        print 'ERROR\nusage: squeeze.py <int: UID> <int: role>'
        sys.exit()

    print("myUID={}, myRole={}".format(my_uid, my_role))

    if my_role == Role.supervisor:
        if  len(sys.argv) == 5:
            upper_bound = int(sys.argv[3])
            sub_range = int(sys.argv[4])
        else:
            print 'ERROR\nusage: squeeze.py <int: UID> <int: role>'
            sys.exit()

        print("upper bound={}, sub range ={}".format(upper_bound, sub_range))

    # create instance of supervisor or worker
    me = None
    if my_role == Role.supervisor:
        me = Supervisor(my_uid, upper_bound, sub_range)
    elif my_role == Role.worker:
        me = Worker(my_uid)
    else:
        print 'ERROR\nusage: squeeze.py <int: UID> <int: role>'
        sys.exit()

    try:
        # create a client instance
        client = mqtt.Client(str(me.uid))
        client.user_data_set(me)

        # setup will for client
        will_message = "Dead UID: {} role: {}".format(me.uid, me.role)
        client.will_set(me.will_topic, will_message)

        # callbacks
        client.on_connect = on_connect
        client.on_publish = on_publish
        client.on_message = on_message
        client.message_callback_add(me.will_topic, on_will)
        client.message_callback_add(me.topic, on_linda)

        # connect to broker
        client.connect(me.broker, me.port, keepalive=me.keepalive)
        while not me.connected:
            client.loop()

        # subscribe to topics
        client.subscribe([(me.topic, me.qos), (me.will_topic, me.qos)])

        me.client = client
        me.duties()
        client.disconnect()
        sys.exit()

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

if __name__ == "__main__":
    main()