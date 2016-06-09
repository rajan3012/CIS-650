"""
CIS 650 
SPRING 2016
Rickie Kerndt <rkerndt@cs.uoregon.edu>

usage: ricart_agrawala.py <int: uid> <int: neighbor1> ... [<int: neighbor2>] [-O] [-L]
    uid: unique identifier
    neighbor1 ... neighborN: peers
    -O: use Carvalho Roucairol optimizations
    -L: lazy mode, peer never requests resource

> For python mosquitto client $ sudo pip install paho-mqtt
> Command line arg to check status of broker $ /etc/init.d/mosquitto status 
"""
import paho.mqtt.client as mqtt
from Queue import Queue, Empty
from random import randint
from threading import Thread, Event
from utility import *

class Role:
    supervisor  = 0
    worker      = 1
    peer        = 2

class Msg:
    request = '0'
    task    = '1'
    result  = '2'
    stop    = '3'
    dead    = '4'
    permission = '5'

class Fake_Message:
    def __init__(self, topic, payload):
        self.mid = 'faux'
        self.topic = topic
        self.payload = payload

class States:
    idle = 0
    gathering = 1
    working = 2
    unwinding = 3

class MQTT:
    """
    Base class provides M2M Messaging Service. Sets up parameters for mosquitto
    and queues messages for publication.
    Requires method definition for processing incoming payloads: processing_incoming()
    """
    def __init__(self, my_uid):
        self.uid = my_uid

        self.client = None
        #self.broker = "white0"
        #self.port = 1883
        self.broker = "brix.d.cs.uoregon.edu"
        self.port = 8100


        # topics
        self.topics = []
        self.will_topic = 'will/'
        self.will_message = None   # must be set by child

        # quality of service
        self.qos = 2
        self.keepalive = 10

        # status attributes
        self.connected = False
        self.abort = False

        # queue of outgoing messages
        self.outgoing = Queue()
        self.pub_pending = False # waiting for a publish confirmation

        # publisher, concurrent thread processing outgoing messages
        self.publisher = Thread(target=self.process_outgoing)
        self.pub_event = Event()

    def register(self):
        """
        Instantiates client, registers call backs, and performs initial subscriptions with broker
        """

        # only once
        if self.connected:
            return

        # create a client instance
        self.client = mqtt.Client(str(self.uid))
        self.client.user_data_set(self)

        # callbacks
        self.client.on_connect = on_connect
        self.client.on_publish = on_publish
        self.client.on_message = on_message
        self.client.message_callback_add(self.will_topic, on_will)
        for topic in self.topics:
            print('setting callback for {} to {}'.format(topic, repr(on_topic)))
            self.client.message_callback_add(topic, on_topic)

        # connect to broker
        self.client.connect(self.broker, self.port, keepalive=self.keepalive)
        while not self.connected:
            self.client.loop()

        # set will
        if self.will_message is not None:
            print('setting will to {}'.format(self.will_message))
            self.client.will_set(self.will_topic, self.will_message)

        # subscribe to topics
        self.client.subscribe([(self.will_topic, self.qos)])
        for topic in self.topics:
            print('subscribing to {}'.format(topic))
            self.client.subscribe([(topic, self.qos)])

        # run network loop from a separate thread
        self.client.loop_start()

        # start publish thread
        self.publisher.start()

    def publish(self, topic,  payload):
        # always push onto queue in case we are processing
        # queue from a different thread
        self.outgoing.put( (topic, payload) )
        print('{} placed msg {}/{} into outgoing queue'.format(self.uid, topic, payload))
        self.pub_event.set()

    def process_outgoing(self):
        """
        Run in a thread to process outgoing queue as messasges are added.
        Spin waits on pub_pending to process all messages in the queue. Once
        queue is empty waits on pub_event
        """

        while not self.abort:
            if not self.pub_pending and not self.outgoing.empty():
                try:
                    topic, payload = self.outgoing.get_nowait()
                except Empty:
                    continue # nothing to do
                self.pub_pending = True
                print("Publishing message {1:}, on topic {0:}".format(topic, payload))
                self.client.publish(topic, payload, self.qos)
                self.outgoing.task_done()
            elif self.outgoing.empty():
                # wait on publish event
                print("{} publisher is waiting for messasges".format(self.uid))
                self.pub_event.wait()
                print("{} publisher is waking up".format(self.uid))
                self.pub_event.clear()


    def check_publish_queue(self):
        """
        non-threaded version
        """
        if not self.pub_pending and not self.outgoing.empty():
            try:
                topic, payload = self.outgoing.get_nowait()
            except Empty:
                return # nothing to do
            self.pub_pending = True
            print("Publishing message {}, on topic {}".format(topic, payload))
            self.client.publish(topic, payload, self.qos)
            self.outgoing.task_done()

    def process_incoming(self, payload):
        """
        Abstract method, child must define to take payload from incoming
        messages to self.uid
        :param payload:
        """
        print('should not be here')

    def set_will(self, uid, role):
        """
        Called by children to set will parameters
        :param uid:
        :param role:
        """
        # setup will for client
        self.will_message = "Dead UID: {} role: {}".format(uid, role)

    def reap(self, uid, role):
        """
        Abstract method called by MQTT for the uid received on a will topic.
        :param uid:
        :param role:
        """
        print('should not be here')

    def disconnect(self):
        """
        Stops network loop and disconnects from broker
        """
        self.client.loop_stop()
        self.client.disconnect()
        self.abort = True
        self.pub_event.set()
        self.publisher.join()


class Ricart_Agrawala(MQTT):
    """
    An implementaton of the Ricart Agrawala mutual exclusion algorithm as described in
    ricart_agrawala_v9.lts
    """

    def __init__(self, uid, role, *neighbors):
        MQTT.__init__(self, uid)
        self.role = role
        self.neighbors = []
        self.topic_prefix = 'ricart_agrawala/'
        self.i_topic = self.topic_prefix + str(uid)
        self.neigh_topics = {}
        self.cs_state = States.idle
        self.clock = 0
        self.req_stamp = 0
        self.count = 0
        self.need = 0
        self.pending = Queue()
        self.lazy = False

        for neigh in neighbors:
            self.neighbors.append(neigh)
            self.neigh_topics[neigh] = self.topic_prefix + str(neigh)

        self.need = len(self.neighbors)

        # setup will for client
        self.set_will(self.uid, self.role)

        # register topics for receiving
        self.topics.append(self.i_topic)

        self.func_critical = None


    def reap(self, uid, role):
        """
        Remove uid from data structures neighors, neigh_topics reducing required count by 1
        :param uid:
        :param role:
        """

        print('{} is reaping {} with role {}'.format(self.uid, uid, role))

        if uid in self.neighbors:
            self.neighbors.remove(uid)
            del(self.neigh_topics[uid])
            self.need -= 1

    def get_topic_uid(self, uid):
        """
        :param uid:
        :return: topic that matches destination uid
        """
        return self.neigh_topics[uid]

    def duties(self):
        """
        Main loop for peer.
        """
        while not self.abort:

            # enter critical section
            if self.count == self.need:
                self.start_critical()

           #self.client.loop()
            self.non_critical_section()

    def start_critical(self):
        self.cs_state = States.working
        if self.func_critical is not None:
            self.func_critical()
            self.func_critical = None
        self.unwind()


    def get_resource(self, func):
        """
        sends requests for permission to all neighbors and sets count to 0
        :param func: is function to call when resource is granted
        """

        if (self.cs_state == States.idle):
            self.cs_state = States.gathering
            self.count = 0
            self.clock += 1
            self.req_stamp = self.clock
            self.func_critical = func

            print('{} changed state to gathering at time {}'.format(self.uid, self.clock))

            for uid, topic in self.neigh_topics.items():
                payload = construct_payload(self.uid, uid, Msg.request, self.clock)
                self.publish(topic, payload)

    def receive_request(self, uid, nt):
        """
        Handles receive requests for all critical section states
        NOTE: ltsa has receive_request ignored when in working or unwinding states. I'm going to
        put these in pending since when doing threaded client.loop() these would
        be interruptable and don't see the harm of adding this logic when not doing threaded
        threaded client.loop()
        :param uid: requestor (src)
        :param nt: requestor's clock value
        """

        # using Lamport's logical clock
        self.clock = max(nt, self.clock) + 1

        if self.cs_state == States.idle:
            self.send_permission(uid)
        elif (self.cs_state == States.gathering) and lambort_lt(uid, nt, self.uid, self.req_stamp):
            self.send_permission(uid)
        else:
            self.pending.put(uid)


    def send_permission(self, uid=None):
        """
        Sends permission to enter critical session to neighbor uid when in CS states idle or gathering.
        When called during unwinding, will send all pending requests for permission.
        Note: even through the Ricart Agrawala protocol does not require the clock for permission message
        the clock is included for consistency in messages and possible implementation of Lamport timestamps.
        :param uid: neighbor to send permission
        """
        suids = []
        if (States.idle <= self.cs_state <=States.gathering) and (uid is not None):
            suids.append(uid)
        elif (self.cs_state == States.unwinding) and self.pending:
            while not self.pending.empty():
                try:
                    nuid = self.pending.get_nowait()
                    suids.append(nuid)
                except Empty:
                    break

        # using Lamport's logical clock
        self.clock += 1

        for nuid in suids:
            payload = construct_payload(self.uid, nuid, Msg.permission, self.clock)
            self.publish(self.get_topic_uid(nuid), payload)

    def receive_permission(self, nt):
        """
        Increments count only when in gathering state.
        """
        # using Lamport's logical clock
        self.clock = max(nt, self.clock) + 1

        if self.cs_state == 1:
            self.count += 1

    def unwind(self):
        """
        Leaving critical section, send any pending permissions
        """
        self.count = 0
        self.cs_state = States.unwinding

        print('{} changed state to unwinding'.format(self.uid))

        self.send_permission()
        self.cs_state = States.idle

    def critical_section(self):
        print('{} is in the critical section at time {} with state {}'.format(self.uid, self.clock, self.cs_state))
        # now sleep for a random interval from
        interruptable_sleep(randint(1,5))

    def non_critical_section(self):
        """
        Sleeps for a random amount of time and the reqeusts
        critical resource
        """
        print('{} is in a non-critical section at time {} with state {}'.format(self.uid, self.clock, self.cs_state))
        # now sleep for a random interval
        interruptable_sleep(randint(0,5))

        if (self.cs_state == States.idle) and not self.lazy:
            self.get_resource(self.critical_section)

    def process_incoming(self, payload):
        """
        :param payload:
        """
        src_uid, dst_uid, msg_type, nt = parse_payload(payload)
        if dst_uid == self.uid:
            print('received msg_type {} from {} at time(nt/local) {}/{} with state {}'.format(msg_type, src_uid, nt, self.clock, self.cs_state))
            if msg_type == Msg.request:
                self.receive_request(src_uid, nt)
            elif msg_type == Msg.permission:
                self.receive_permission(nt)

class Carvalho_Roucairol(Ricart_Agrawala):
    """
    adds the Carvalho Roucairol optimizations to Ricart Agrawala. Implemented in the design of
    ricart_agrawala_psuedo_code.pdf.
    """
    def __init__(self,uid, role, *neighbors):
        """
        Adds reqeusts set, to track which neighbors have actually requested the resource. Basis of
        optimization is to not request permission from a peer that is not using the resource.
        :param uid:
        :param neighbors:
        """

        Ricart_Agrawala.__init__(self, uid, role,  *neighbors)

        # added data structure to track neighbors who have requested the critical resource
        self.requests = set()

        # at initialization want to seek permission from all neighbors
        for neigh in self.neighbors:
            self.requests.add(neigh)

    def reap(self, uid, role):
        """
        Call parent reap() and then remove uid from self.requests, if count is now sufficient call the
        critical section from here.
        """

        Ricart_Agrawala.reap(self, uid, role)

        if uid in self.requests:
            self.requests.remove(uid)

        if self.cs_state == States.gathering:
            self.need = len(self.requests)
            if self.count == self.need:
                self.start_critical()

    def duties(self):
        """
        Main loop for peer.
        Note: critical section is entered from receive_permission or get_resource
        """
        while not self.abort:
            self.non_critical_section()

    def get_resource(self, func):
        """
        sends requests for permission to neighbors using resource and sets count to 0.
        If no requests have been received then safe to proceed.
        :param func: is function to call when resource is granted
        """

        if self.cs_state == States.idle:
            self.count = 0
            self.clock += 1
            self.req_stamp = self.clock
            self.func_critical = func

            if self.requests:
                self.cs_state = States.gathering
                print('{} changed state to gathering at time {}'.format(self.uid, self.clock))

                # set self.need to request queue size
                self.need = len(self.requests)

                while self.requests:
                    uid = self.requests.pop()
                    payload = construct_payload(self.uid, uid, Msg.request, self.clock)
                    self.publish(self.get_topic_uid(uid), payload)
            else:
                self.start_critical()

    def receive_permission(self, nt):
        """
        Enters critical section when permission count equals number of requests that
         were sent.
         Note: self.need is updated by get_resource
        :return:
        """
        Ricart_Agrawala.receive_permission(self, nt)
        print('{} has {} needs {}'.format(self.uid, self.count, self.need))
        if self.count == self.need:
            self.start_critical()

    def send_permission(self, uid=None):
        """
        Copies all pending into requests
        :param uid:
        """

        suids = []
        if (States.idle <= self.cs_state <= States.gathering) and (uid is not None):
            suids.append(uid)
            self.requests.add(uid)
        elif (self.cs_state == States.unwinding) and self.pending:
            while not self.pending.empty():
                try:
                    nuid = self.pending.get_nowait()
                    suids.append(nuid)
                    self.requests.add(nuid)
                except Empty:
                    break

        # using Lamport's logical clock
        self.clock += 1

        for nuid in suids:
            payload = construct_payload(self.uid, nuid, Msg.permission, self.clock)
            self.publish(self.get_topic_uid(nuid), payload)

    def receive_request(self, uid, nt):
        """
        Adds a requestor to requests so that we ask them for permission later
        :param uid: requestor (src)
        :param nt: requestor's clock value
        """

        # using Lamport's logical clock
        self.clock = max(nt, self.clock) + 1

        if self.cs_state == States.idle:
            self.send_permission(uid)
            self.requests.add(uid)
        elif (self.cs_state == States.gathering) and lambort_lt(uid, nt, self.uid, self.req_stamp):
            self.send_permission(uid)
            self.requests.add(uid)
            # send a request to requester
            payload = construct_payload(self.uid, uid, Msg.request, self.clock)
            self.publish(self.get_topic_uid(uid), payload)
        else:
            self.pending.put(uid)


'''
---------------------------------------------------------------------
    MQTT callbacks
---------------------------------------------------------------------
'''

def on_connect(client, userdata, flags, rc):
    """
    Called when the broker responds to our connection request
    :param client:
    :param userdata:
    :param flags:
    :param rc:
    """
    if rc != 0:
        print("Connection failed. RC: " + str(rc))
    else:
        print("Connected successfully with result code RC: " + str(rc))
        userdata.connected = True


def on_publish(client, userdata, mid):
    """
    Called when a published message has completed transmission to the broker
    :param client:
    :param userdata:
    :param mid:
    """
    print("Message ID "+str(mid)+ " successfully published")
    userdata.pub_pending = False



def on_will(client, userdata, msg):
    """
    Called when message received on will_topic
    :param client:
    :param userdata:
    :param msg:
    """
    print("Received message [{}]: {} on topic {}".format(msg.mid, msg.payload, msg.topic))

    # call reap() with uid and role of deceased
    fields = msg.payload.split(' ')
    dead_uid = int(fields[2])
    dead_role = int(fields[4])
    userdata.reap(dead_uid, dead_role)

def on_message(client, userdata, msg):
    """
    Called when a message has been received on a subscribed topic (unfiltered)
    :param client:
    :param userdata:
    :param msg:
    """
    print("Received message [{}]: {} on topic {}".format(msg.mid, msg.payload, msg.topic))
    print('unfiltered message')


def on_topic(client, userdata, msg):
    """
    Callback method for topic
    :param client:
    :param userdata:
    :param msg:
    """
    print("Received message [{}]: {} on topic {}".format(msg.mid, msg.payload, msg.topic))
    userdata.process_incoming(msg.payload)


'''
-------------------------------------------------------------------
    Utility methods
-------------------------------------------------------------------
'''

def parse_msg(msg):
    topic = msg.topic
    src_uid, dst_uid, msg_type, payload = parse_payload(msg.payload)
    return topic, src_uid, dst_uid, msg_type


def parse_payload(msg):
    """
    parse MQTT.msg.payload, there is an unfortuante double usage of payload
    """
    src_uid, dst_uid, msg_type, payload = msg.split(':', 3)
    try:
        src_uid = int(src_uid)
        dst_uid = int(dst_uid)
    except ValueError:
        return None

    return src_uid, dst_uid, msg_type, payload

def construct_payload(src_uid, dst_uid, msg_type, payload='None'):
    return ':'.join([str(src_uid), str(dst_uid), msg_type, str(payload)])

def lambort_lt(uid1, clock1, uid2, clock2):
    """
    Compares two Lambort logical clocks using uid as the tie breaker to provide total ordering
    in a distributed system.
    :param uid1:
    :param clock1:
    :param uid2:
    :param clock2:
    :return: True if clock1 < clock2 or uid1 < uid2 when clock1 = clock2
    """
    result = False
    if clock1 < clock2:
        result = True
    elif (clock1 == clock2) and (uid1 < uid2):
        result = True
    return result


