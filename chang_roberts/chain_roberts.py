"""
CIS 650 
SPRING 2016
usage: pass_token_mqtt.py <UID> <upstream UID>

> For python mosquitto client $ sudo pip install paho-mqtt
> Command line arg to check status of broker $ /etc/init.d/mosquitto status 
"""
import sys
import time
import paho.mqtt.client as mqtt
from grovepi import *
from time import sleep
#from enum import Enum


class States:
    active = 0
    decide = 1
    passive = 2
    announce = 3
    wait = 4
    working = 5


class MQTT_data:

    def __init__(self, UID, upstream_UID):
        #self.States = Enum('active', 'decide', 'passive', 'announce', 'wait', 'working')
        self.UID = UID
        self.upstream_UID = upstream_UID
        self.broker = "brix.d.cs.uoregon.edu"
        self.port = 8100
        self.send_token_topic = 'token/' + str(upstream_UID)
        self.will_topic = 'will/'
        self.publish_topic = 'token/' + str(UID)
        self.subscribe_topic = 'token/' + str(upstream_UID)
        self.will_message = "Dead UID: {}, upstream_UID: {} ".format(UID, upstream_UID)
        self.qos = 1
        self.keepalive = 30
        self.state = States.active
        self.active = False
        self.leader = None
        self.connected = False
        self.wait_on_publish = False

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
    userdata.wait_on_publish = False

#Called when message received on token_topic

def on_token(client, userdata, msg):
    print("Received message: "+str(msg.payload)+". On topic: "+msg.topic)
    time.sleep(2)
    client.publish(userdata.send_token_topic, userdata.UID)

#Called when message received on will_topic
def on_will(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)

#Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    print('unfiltered message')

# Use a single callback select by state, basically replace former call backs with elif blocks
def on_topic(client, userdata, msg):

    if userdata.state == States.active:
        print "in active--- msg received: {}".format(msg.payload)
        message_name, uid = parse_msg(msg.payload)

        if message_name == 'send_id':
            decide(client, userdata, uid)
        elif message_name == 'send_leader':
            send_leader(client, userdata, uid)
            working(client, userdata)

    elif userdata.state == States.passive:
        print "in passive--- msg received: {}".format(msg.payload)
        message_name, uid = parse_msg(msg.payload)

        if message_name == 'send_leader':
            userdata.leader = uid
            print "Accepted {} as my leader".format(userdata.leader)
            send_leader(client, userdata, uid)
            working(client, userdata)
        elif message_name == 'send_id':
            send_uid(client, userdata, uid)

    elif userdata.state == States.wait:
        print "in wait--- msg received: {}".format(msg.payload)
        message_name, uid = parse_msg(msg.payload)

        if message_name == 'send_leader':
            print "Leader announce has gone full circle"
            working(client, userdata)

    elif userdata.state == States.working:
        #if msg.payload.startswith('count_primes'):
        if msg.payload.startswith('blink_LED'):
            #msg_list = msg.payload.split(':')
            #lower_bound = int(msg_list[1])
            #count = int(msg_list[2])

            # send message to get others started
            #send_primes(client, userdata, lower_bound + 100001, count + 1)
            send_token(client, userdata)
            # start our count
            #print "counting primes {}:{}".format(lower_bound, lower_bound+100000)
            print "blinking LED"
            #count_primes(lower_bound, lower_bound + 100000)

    else:
        print "ERROR: in an undefined state!"

################################################
## State Functions
################################################
def decide(client, userdata, uid):
    print "State changed to decide"
    userdata.state = States.decide
    print "uid={} userdata.UID={}".format(uid, userdata.UID)

    if uid > userdata.UID:
        send_uid(client, userdata, uid)
        passive(client, userdata)
        return
    elif uid == userdata.UID:
        print "I, {},  am the leader".format(userdata.UID)
        announce(client, userdata)
        return

    print "Going back to active"
    userdata.active == True
    active(client, userdata)

def announce(client, userdata):
    print "State changed to announce"
    userdata.state = States.announce
    userdata.leader = userdata.UID
    send_leader(client, userdata, userdata.UID)
    wait(client, userdata)

def working(client, userdata):
    print "State changed to working"
    userdata.state = States.working
    if userdata.leader == userdata.UID:
        print "I'm the leader so let's get busy"
        #send_primes(client, userdata, 3, 1)
        send_token(client,userdata)

def active(client, userdata):
    print "State changed to active:{}".format(userdata.active)
    userdata.state = States.active

    # TODO  active should always be True, remove?
    if userdata.active == False:
        send_uid(client, userdata, userdata.UID)

def passive(client, userdata):
    print("State changed to passive")
    userdata.state = States.passive


def wait(client, userdata):
    print("State changed to wait for round trip")
    userdata.state = States.wait


################################################
## Publish functions
################################################

def send_uid(client, userdata, uid):
    payload = 'send_id:' + str(uid)
    print "Publishing msg {} on {}".format(payload,userdata.publish_topic)
    client.publish(userdata.publish_topic, payload,userdata.qos, True)
    userdata.wait_on_publish = True

def send_leader(client,userdata, uid):
    payload = 'send_leader:' + str(uid)
    print "Publishing msg {} to {}".format(payload,userdata.publish_topic)
    client.publish(userdata.publish_topic, payload, userdata.qos, True)
    userdata.wait_on_publish = True

def send_primes(client, userdata, lower_bound, count):
    payload = 'count_primes:' + str(lower_bound) + ':' + str(count)
    print "Publishing msg {} to {}".format(payload,userdata.publish_topic)
    client.publish(userdata.publish_topic, payload, userdata.qos, True)
    userdata.wait_on_publish = True

def send_token(client,userdata):
    payload = 'blink_LED:'
    print "Publishing msg {} to {}".format(payload, userdata.publish_topic)
    client.publish(userdata.publish_topic, payload, userdata.qos, True)
    userdata.wait_on_publish = True

##################################################
## Utility functions
##################################################
def parse_msg(msg):
    msg_list = msg.split(':')
    message_name = msg_list[0]
    uid = int(msg_list[1])
    return message_name, uid

def count_primes(lower_bound, upper_bound):
    from math import sqrt, ceil
    from timeit import default_timer as timer

    count = 0

    start = timer()

    for n in range(lower_bound, upper_bound):
        upper = int(ceil(sqrt(n)))
        for i in range(2, upper):
            if n % i != 0:
                break
            count += 1

    end = timer()

    print "Found {} primes between {} and {} in {}".format(count, lower_bound, upper_bound, end-start)

def blink_led():
    led = 4
    pinMode(led, "output")
    digitalWrite(led,1)
    time.sleep(1)
    digitalWrite(led,0)

def main():
    #############################################
    ## Get UID and upstram_UID from args
    #############################################

    if len(sys.argv) != 3:
        print
        'ERROR\nusage: chain_roberts.py <int: UID> <int: upstream UID>'
        sys.exit()

    try:
        UID = int(sys.argv[1])
        upstream_UID = int(sys.argv[2])
    except ValueError:
        print()
        'ERROR\nusage: chain_roberts.py <int: UID > <int: upstream UID >'
        sys.exit()

    #############################################
    ## MQTT settings
    #############################################

    myMQTT = MQTT_data(UID, upstream_UID)

    #############################################
    ## Connect to broker and subscribe to topics
    #############################################
    try:
        # create a client instance
        client = mqtt.Client(str(myMQTT.UID), clean_session=True)

        # setup will for client
        client.will_set(myMQTT.will_topic, myMQTT.will_message)

        # setup userdata for client
        client.user_data_set(myMQTT)

        # callbacks
        client.on_connect = on_connect
        client.on_publish = on_publish
        client.on_message = on_message

        # callbacks for specific topics
        client.message_callback_add(myMQTT.will_topic, on_will)
        client.message_callback_add(myMQTT.subscribe_topic, on_topic)
        myMQTT.active = True

        # connect to broker
        client.connect(myMQTT.broker, myMQTT.port, keepalive=(myMQTT.keepalive))

        # spin wait on connect until we do anything else
        print "waiting for connect ..."
        while not myMQTT.connected:
            client.loop()


        # subscribe to list of topics
        client.subscribe([(myMQTT.subscribe_topic, myMQTT.qos),
                          (myMQTT.will_topic, myMQTT.qos),
                          ])

        # initiate first publish of ID for leader election
        send_uid(client, myMQTT, myMQTT.UID)

        # spin wait on publish
        while myMQTT.wait_on_publish:
            client.loop()

        # main loop
        while(True):

            blink_led()

            # if elif blocks for each state
            if myMQTT.state == States.active:
                pass
            elif myMQTT.state == States.announce:
                pass
            elif myMQTT.state == States.decide:
                pass
            elif myMQTT.state == States.passive:
                pass
            elif myMQTT.state == States.wait:
                pass
            elif myMQTT.state == States.working:
                #TODO call working functions here
                pass
            else:
                pass

            # block for message send/receive
            print "going into client.loop"
            client.loop(myMQTT.keepalive // 3)
            print "exiting client loop"

            # spin wait on publish
            while myMQTT.wait_on_publish:
                client.loop()

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

if __name__ == "__main__":
    main()