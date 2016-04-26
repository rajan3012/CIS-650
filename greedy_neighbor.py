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
    field  = 0
    gate   = 1
    neigh1 = 2
    neigh2 = 3

class Msg:
    false           = '0'
    true            = '1'
    set_flag1_true  = '2'
    set_flag1_false = '3'
    set_flag2_true  = '4'
    set_flag2_false = '5'
    test_flag1      = '6'
    set_card_1      = '7'
    set_card_2      = '8'
    rslt_flag1      = '9'
    test_flag2      = 'a'
    rslt_flag2      = 'b'
    enter_field     = 'c'
    exit_field      = 'd'


class Health:
    strong = 0
    weak   = 1

class Field:


    def __init__(self):
        self.id = Role.field
        self.occupants = set()


class Gate:

    def __init__(self):
        self.id = Role.gate
        self.flag1 = Msg.false
        self.flag2 = Msg.false
        self.card = -1

class Neighbor:

    # states that a neighbor may have
    INIT    = 0
    FLAG    = 1
    CARD    = 2
    REQUEST = 3
    TEST    = 4
    FIELD   = 5
    EXIT    = 6

    def __init__(self, n):
        self.id = None
        if n == Role.neigh1:
            self.id = Role.neigh1
        elif n == Role.neigh2:
            self.id = Role.neigh2

        self.strength = Health.strong
        self.state = Neighbor.INIT

        self.send_set_flag_false = None
        self.send_set_flag_true = None
        self.send_set_card = None
        self.send_test_flag = None
        self.rslt_flag = None

        # set which flags/card values to use
        if self.id == Role.neigh1:
            self.send_set_flag_false = Msg.set_flag1_false
            self.send_set_flag_true = Msg.set_flag1_true
            self.send_set_card = Msg.set_card_2
            self.send_test_flag = Msg.test_flag2
            self.rslt_flag = Msg.rslt_flag2
        elif self.id == Role.neigh2:
            self.send_set_flag_false = Msg.set_flag2_false
            self.send_set_flag_true = Msg.set_flag2_true
            self.send_set_card = Msg.set_card_1
            self.send_test_flag = Msg.test_flag1
            self.rslt_flag = Msg.rslt_flag1


#############################################
## MQTT settings
#############################################
class MQTT:
    def __init__(self, my_uid, role):
        self.uid = my_uid
        self.role = role

        if role == Role.field:
            print("Configuring as a field")
            self.role = Field()
        elif role == Role.gate:
            print("Configuring as a gate")
            self.role = Gate()
        elif role == Role.neigh1:
            print("Configuring as Neighbor 1")
            self.role = Neighbor(role)
        elif role == Role.neigh2:
            print("Configuring as Neighbor 2")
            self.role = Neighbor(role)

        self.broker = "white0"
        self.port = 1883

        # topics
        self.field_topic = 'Field'
        self.gate_topic = 'Gate'
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

def on_gate(client, userdata, msg):
    print("Gate | Received message: " + str(msg.payload) + "on topic: " + msg.topic)
    print("flag1={}, flag2={}, card={}".format(userdata.role.flag1,userdata.role.flag2,userdata.role.card))
    msg_type , value = parse_msg(msg)

    if (msg_type == Msg.set_flag1_true):
        userdata.role.flag1 = Msg.true
    elif (msg_type == Msg.set_flag1_false):
        userdata.role.flag1 = Msg.false
    elif (msg_type == Msg.set_flag2_true):
        userdata.role.flag2 = Msg.true
    elif (msg_type == Msg.set_flag2_false):
        userdata.role.flag2 = Msg.false
    elif (msg_type == Msg.set_card_1):
        userdata.role.card = 1
    elif (msg_type == Msg.set_card_2):
        userdata.role.card = 2
    elif (msg_type == Msg.test_flag1):
        if(userdata.role.flag1 == Msg.true and userdata.role.card==1):
            print("N1 in field. Wait your turn N2")
            publish(client, userdata, userdata.gate_topic, Msg.rslt_flag1 + ':' + Msg.false)
        else:
            print("N1 can enter the field")
            publish(client, userdata, userdata.gate_topic, Msg.rslt_flag1 + ':' + Msg.true)
    elif (msg_type == Msg.test_flag2):
        if (userdata.role.flag2 == Msg.true and userdata.role.card == 2):
            print("N2 in field. Wait your turn N1")
            publish(client, userdata, userdata.gate_topic, Msg.rslt_flag2 + ':' + Msg.false)
        else:
            print("N2 can enter the field")
            publish(client, userdata, userdata.gate_topic, Msg.rslt_flag2 + ':' + Msg.true)


#Callback method for neighbor roles
def on_neighbor(client, userdata, msg):
    msg_type, value = parse_msg(msg)
    print("msg_type={}, value={}, state={} role.rslt_flag={}".format(msg_type,value,userdata.role.state,userdata.role.rslt_flag))
    if (msg_type == userdata.role.rslt_flag) and (userdata.role.state == Neighbor.TEST):
        if value == int(Msg.true):
            # enter the field
            print("Entering the field")
            client.publish(userdata.field_topic, Msg.enter_field + ':' + str(userdata.uid))
            userdata.role.state = Neighbor.FIELD
        else:
            print("Neighbor is still in the field")
            userdata.role.state = Neighbor.REQUEST

def on_field(client, userdata, msg):

    msg_type, value = parse_msg(msg)

    if msg_type == Msg.enter_field:
        userdata.role.occupants.add(value)
        print("Neighbor {} has entered the field".format(value))
    elif msg_type == Msg.exit_field:
        if value in userdata.role.occupants:
            print("Neighbor {} is leaving the field".format(value))
            userdata.role.occupants.remove(value)
        else:
            print("ERROR: Neighbor {} is not in field".format(value))

    print("The field now holds {}".format(userdata.role.occupants.__repr__()))


#############################################
## Utility methods
#############################################

def parse_msg(msg):
    msg_list = msg.split(':')
    message_name = msg_list[0]
    uid = int(msg_list[1])
    return message_name, uid

def publish(client, userdata, topic, payload):
    #print("Entered publish with {}/{}".format(topic,payload))
    if userdata.pending or not userdata.queue.empty():
      #print("Queueing message")
        userdata.queue.put( (topic, payload) )  # this is a blocking put
    else: # if the queue is empty and nothing pending just go ahead and publish
        #print("Sending message straight out")
        userdata.pending = True
        client.publish(topic, payload, userdata.qos)

def check_publish_queue(client, userdata):
    #print("Checking for queued messages")
    if not userdata.pending and not userdata.queue.empty():
        try:
            topic, payload = userdata.queue.get()
        except Empty:
            return # nothing to do
        userdata.pending = True
        #print("Sending queued message")
        client.publish(topic, payload, userdata.qos)

def parse_msg(msg):
    msg_list = msg.payload.split(':')
    message_name = msg_list[0]
    uid = int(msg_list[1])
    return message_name, uid


#############################################
## Role methods
#############################################

def field(client, userdata):

    client.message_callback_add(userdata.field_topic, on_field)
    client.subscribe(userdata.field_topic, userdata.qos)

    while not userdata.abort:
        client.loop()


def gate(client, userdata):

    client.message_callback_add(userdata.gate_topic, on_gate)
    client.subscribe(userdata.gate_topic, userdata.qos)

    #main processing loop
    while not userdata.abort:
        check_publish_queue(client, userdata)
        #do something
        client.loop()



def neighbor(client, userdata):

    def do_chores():
        sleep(1)
        userdata.role.strength = Health.weak

    def strong():
        # returns true if strong. derive some function
        # food
        return userdata.role.strength == Health.strong

    client.message_callback_add(userdata.gate_topic, on_neighbor)
    client.subscribe(userdata.gate_topic, userdata.qos)

    # Main processing loop, cycle between doing chores and getting food
    while not userdata.abort:

        # sending any queued messages
        check_publish_queue(client, userdata)

        if strong():
            print("Feeling strong, doing chores")
            do_chores()

        # get some food when not doing chores
        if not userdata.pending:
            if userdata.role.state == Neighbor.INIT:
                print("Set my flag true")
                userdata.role.state = Neighbor.FLAG
                publish(client, userdata, userdata.gate_topic, userdata.role.send_set_flag_true + ':' + str(userdata.uid))
            elif userdata.role.state == Neighbor.FLAG:
                print("Set card to my neighbor's turn")
                userdata.role.state = Neighbor.REQUEST
                publish(client, userdata, userdata.gate_topic, userdata.role.send_set_card + ':' + str(userdata.uid))
            elif (userdata.role.state == Neighbor.REQUEST):
                print("Requesting entry into field")
                userdata.role.state = Neighbor.TEST
                publish(client, userdata, userdata.gate_topic, userdata.role.send_test_flag + ':' + str(userdata.uid))
            elif (userdata.role.state == Neighbor.FIELD):
                print("Gathering food")
                sleep(1)
                print("Exiting field")
                userdata.role.state = Neighbor.EXIT
                publish(client, userdata, userdata.field_topic, Msg.exit_field + ':' + str(userdata.uid))
            elif (userdata.role.state == Neighbor.EXIT):
                print("Set my flag to false")
                userdata.role.state = Neighbor.INIT
                userdata.role.strength = Health.strong
                publish(client, userdata, userdata.gate_topic, userdata.role.send_set_flag_false + ':' + str(userdata.uid))

        # slow things down
        sleep(3)

        # check for messages
        client.loop()


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

        if me.role.id == Role.field:
            field(client, me)
        elif me.role.id == Role.gate:
            gate(client, me)
        elif (me.role.id == Role.neigh1) or (me.role.id == (Role.neigh2)):
            neighbor(client, me)

        client.disconnect()
        sys.exit()

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

if __name__ == "__main__":
    main()