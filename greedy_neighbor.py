"""
CIS 650 
SPRING 2016
usage: greedy_neighbor.py <UID> <field(0), gate(1), neighbor1(2) , neighbor2(3)>

> For python mosquitto client $ sudo pip install paho-mqtt
> Command line arg to check status of broker $ /etc/init.d/mosquitto status 
"""
import sys
import time
import paho.mqtt.client as mqtt


class Role:

    field = 0
    gate = 1
    neigh1 = 2
    neigh2 = 3

class Field:

    def __init__(self):
        self.id = Role.field

class Gate:

    def __init__(self):
        self.id = Role.gate

class Neighbor:

    def __init__(self, n):
        if n == 1:
            self.id = Role.neigh1
        elif n == 2:
            self.id = Role.neigh2
        else:
            self.id = None

#############################################
## MQTT settings
#############################################
class MQTT:
    def __init__(self, my_uid, role):
        self.uid = my_uid
        self.role = None

        if role == Role.field:
            self.role = Field()
        elif role == Role.gate:
            self.role = Gate()
        elif role == Role.neigh1:
            self.role = Neighbor(1)
        self.port        = 1883

        # topics
        self.field_topic = 'Field'
        self.gate_topic = 'Gate'
        self.will_topic = 'will/'

        #quality of service
        self.qos = 1
        self.keepalive = 30


        self.connected = False
        self.abort = False

        # queue of outgoing messages
        self.queue = []
        self.pending = False # waiting for a publish confirmation

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
    userdata.pending == False


#Called when message received on will_topic
def on_will(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    userdata.abort = True

#Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    print('unfiltered message')

def on_gate(client, userdata, msg):
    print("Gate | Received message: " + str(msg.payload) + "on topic: " + msg.topic)
    message_name, uid, flag_value , turn = parse_msg(msg.payload)
    if(flag_value == 'True'): #neighbour is trying to enter the field

    # do something with message
    pass

def on_neighbor(client, userdata, msg):
    pass

def on_field(client, userdata, msg):

#############################################
## Utility methods
#############################################

def parse_msg(msg):
    msg_list = msg.split(':')
    message_name = msg_list[0]
    uid = int(msg_list[1])
    return message_name, uid

def publish(client, userdata, topic, payload):

    if userdata.pending:
        userdata.queue.append( (topic, payload) )
    elif len(userdata.queue) == 0:
        client.publish(topic, payload, userdata.qos)

def check_publish_queue(client, userdata):

    if not userdata.pending && len(userdata.queue) > 0:
        topic, payload = userdata.queue.pop()
        userdata.pending == True
        client.publish(topic, payload, userdata.qos)


#############################################
## Role methods
#############################################

def field(client, userdata):
    pass

def gate(client, userdata):

    client.message_callback_add(userdata.gate_topic, on_gate)

    #main processing loop
    while not userdata.abort:
        check_publish_queue(client, userdata)
        #do something

    pass

def neighbor1(client, userdata):

    client.message_callback_add(userdata.gate_topic, on_neighbor)

    # Main processing loop
    while not userdata.abort:
        check_publish_queue(client, userdata.qos)
        client.loop()


def neighbor2(client, userdata):
    pass

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
        print 'ERROR\nusage: greedy_neighbor.py <int: UID> <int: field UID> <int: gate UID>'
        sys.exit()

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

        if me.role == Role.field:
            field(client, me)
        elif me.role == Role.gate:
            gate(client, me)
        elif me.role == Role.neigh1:
            neighbor1(client, me)
        elif me.role == Role.neigh2:
            neighbor2(client, me)

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

