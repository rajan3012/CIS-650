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

class Role:
    supervisor  = 0
    worker   = 1

class Msg:
    request = '0'
    task    = '1'
    result  = '2'

class Task:
    def __init__(self, uid, lo, up, worker_uid = None):
        self.uid = uid
        self.lo = lo
        self.up = up
        self.worker_uid = worker_uid
        self.result = None

    @classmethod
    def from_payload(cls, payload):
        uid, lo, up, worker_uid = payload.split(':')
        return cls(uid, lo, up, worker_uid)

    def __str__(self):
        s = Msg.task
        if self.result is not None:
            s = Msg.result
        return ':'.join(s, str(self.uid), str(self.lo), str(self.up), str(self.worker_uid, str(self.result)))


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
        self.qos = 1
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

            # check to see if any tasks have been sent
            msg = None
            try:
                msg = self.incoming.get_nowait()
            except Empty:
                # don't see this as a good use of exceptions
                pass
            if msg is not None:
                src_uid, dst_uid, msg_type, payload = parse_msg(msg)
                if msg_type is Msg.task:
                    self.request_sent = False
                    my_task = Task.from_payload(payload)
                    my_task.result = mp_count_primes(my_task.lo, my_task.up)
                    payload = str(my_task)
                    msg = ':'.join(['0',self.uid, payload])
                    self.publish(msg)

            self.check_publish_queue()

            if not self.request_sent:
                msg = ':'.join([self.uid, '0', Msg.request])
                self.publish(msg)

            self.client.loop()

class Supervisor:

    def __init__(self, uid, upper, range):
        MQTT.__init__(self, uid)
        self.role = Role.supervisor
        self.upper = upper
        self.range = range
        self.bag = Queue()
        self.pending = {}
        self.results = {}

    def duties(self):
        # main loop for a supervisor
        pass


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
    userdata.abort = True

#Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    print('unfiltered message')

#Callback method for LINDA topic
def on_linda(client, userdata, msg):
    src_uid, dst_uid, msg_type, payload = parse_msg(msg)
    print("Received msg id={}, type={}, src={}, dst={}, payload={}".format(msg.id, msg_type, src_uid, dst_uid, payload))

    if dst_uid == userdata.uid:
        userdata.incoming.put(msg)

#############################################
## Utility methods
#############################################
def parse_msg(msg):
    msg_list = msg.payload.split(':')
    src_uid = msg_list[0]
    dst_uid = msg_list[1]
    msg_type = msg_list[2]
    payload = msg_list[3:]
    return src_uid, dst_uid, msg_type, payload

def chunks(lo, up, sub_range):
    lo_sub = lo
    up_sub = lo + sub_range
    while up_sub <= up:
        yield lo_sub, up_sub
        lo_sub = up_sub + 1
        up_sub = up_sub + sub_range

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
            p_range = int(sys.argv[4])
        else:
            print 'ERROR\nusage: squeeze.py <int: UID> <int: role>'
            sys.exit()

    print("lower bound={}, upper bound ={}")

    # create instance of supervisor or worker
    me = None
    if my_role == Role.supervisor:
        me = Supervisor(my_uid)
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
        client.subscribe([(me.topic, me.qos), (me.will_topic, on_will)])

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