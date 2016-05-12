"""
CIS 650 
SPRING 2016
usage: greedy_neighbor.py <UID> <field(0), gate(1), neighbor1(2) , neighbor2(3)>

> For python mosquitto client $ sudo pip install paho-mqtt
> Command line arg to check status of broker $ /etc/init.d/mosquitto status 
"""
import sys
from time import sleep
import paho.mqtt.client as mqtt
from Queue import Queue, Empty

class Role:
    supervisor  = 0
    worker   = 1

class Msg:
    request = '0'
    task    = '1'
    result  = '2'


class Supervisor:

    def __init__(self, upper, range):
        self.upper = upper
        self.range = range
        self.bag = Queue()
        self.pending = {}
        self.results = {}


    def duties(self):
        # main loop for a supervisor
        pass

class Worker:
    def __init__(selfs):
        pass

    def duties(self):
        # main loop for a worker
        pass

    # import multi-process primes here

#############################################
## MQTT settings
#############################################
class MQTT:
    def __init__(self, my_uid, role):
        self.uid = my_uid
        self.role = role

        if role == Role.supervisor:
            print("Configuring as a supervisor")
            self.role = Supervisor()
        elif role == Role.worker:
            print("Configuring as a worker")
            self.role = Worker()

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
        self.queue = Queue()
        self.pending = False # waiting for a publish confirmation

        # queue of incoming messages
        self.incoming = Queue()

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
    userdata.pending = False


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

    msg_type, payload = parse_msg(msg)
    print("Received msg id={}, type={}, payload={}".format(msg.id, msg_type, payload))


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

def publish(client, userdata, topic, payload):
    if userdata.pending or not userdata.queue.empty():
        userdata.queue.put( (topic, payload) )  # this is a blocking put
    else: # if the queue is empty and nothing pending just go ahead and publish
        userdata.pending = True
        print("Publishing {},{}".format(topic, payload))
        client.publish(topic, payload, userdata.qos)

def check_publish_queue(client, userdata):
    if not userdata.pending and not userdata.queue.empty():
        try:
            topic, payload = userdata.queue.get()
        except Empty:
            return # nothing to do
        userdata.pending = True
        print("Publishing {},{}".format(topic, payload))
        client.publish(topic, payload, userdata.qos)


#############################################
## Main method takes command line arguments initialize and call role
#############################################

def main():


    if len(sys.argv) != 3:
        print 'ERROR\nusage: greedy_neighbor.py <int: UID> <int: field UID> <int: gate UID>'
        sys.exit()

    try:
        my_uid = int(sys.argv[1])
        my_role = int(sys.argv[2])
    except ValueError:
        print 'ERROR\nusage: greedy_neighbor.py <int: UID> <int: roleD>'
        sys.exit()

    print("myUID={}, myRole={}".format(my_uid, my_role))
    me = MQTT(my_uid, my_role)

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

        # connect to broker
        client.connect(me.broker, me.port, keepalive=me.keepalive)
        while not me.connected:
            client.loop()

        if me.role.id == Role.supervisor:
            me.role = Supervisor(upper_bound, p_range)
            me.role.duties()
        elif me.role.id == Role.worker:
            me.role = Supervisor()
            me.role.duties()

        client.disconnect()
        sys.exit()

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

if __name__ == "__main__":
    main()