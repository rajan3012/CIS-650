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
        self.broker = "white0"
        self.port = 1883
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

##############################################
## MQTT callbacks
##############################################

#Called when the broker responds to our connection request
def on_connect(client, userdata, flags, rc):
    if rc != 0:
        print("Connection failed. RC: " + str(rc))
    else:
        print("Connected successfully with result code RC: " + str(rc))

#Called when a published message has completed transmission to the broker
def on_publish(client, userdata, mid):
    print("Message ID "+str(mid)+ " successfully published")

#Called when message received on token_topic
'''
def on_token(client, userdata, msg):
    print("Received message: "+str(msg.payload)+". On topic: "+msg.topic)
    time.sleep(2)
    client.publish(userdata.send_token_topic, userdata.UID)'''

#Called when message received on will_topic
def on_will(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)

#Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    print('unfiltered message')

#Active state waiting for send_id or send_leader
def on_active(client, userdata, msg):
    print("In active--- msg received:",msg.payload)
    print msg.payload.split(':')
    message_name, uid = parse_msg(msg.payload)

    if message_name == 'send_id':
        decide(client, userdata, uid)
    elif message_name == 'send_leader':
        send_leader(client, userdata, uid)
        working(client,userdata)

def on_passive(client, userdata, msg):
    print("In passive--- msg received:", msg.payload)
    message_name, uid = parse_msg(msg.payload)

    if message_name == 'send_leader':
        userdata.leader = uid
        print "Accepted {} as my leader".format(userdata.leader)
        working(client, userdata)
    elif message_name == 'send_id':
        send_uid(client, userdata, uid)

def on_wait(client, userdata, msg):
    print("In wait--- msg received:", msg.payload)
    message_name, uid = parse_msg(msg.payload)

    if message_name == 'send_leader':
        print "Leader announce has gone full circle"
        working(client, userdata)

def on_working(client, userdata, msg):
    print "Supposed to be working but have nothing to do"

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
    elif uid == userdata.UID:
        print "I, {},  am the leader".format(userdata.UID)
        announce(client, userdata)

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
    client.message_callback_remove(userdata.subscribe_topic)
    client.message_callback_add(userdata.subscribe_topic, on_working)


def active(client, userdata):
    print "State changed to active:{}".format(userdata.active)
    userdata.state = States.active

    # TODO  active should always be True, remove?
    if userdata.active == False:
        send_uid(client, userdata, userdata.UID)

    client.message_callback_remove(userdata.subscribe_topic)
    client.message_callback_add(userdata.subscribe_topic, on_active)

def passive(client, userdata):
    print("State changed to passive")
    userdata.state = States.passive

    client.message_callback_remove(userdata.subscribe_topic)
    client.message_callback_add(userdata.subscribe_topic, on_passive)

def wait(client, userdata):
    print("State changed to wait for round trip")
    userdata.state = States.wait

    client.message_callback_remove(userdata.subscribe_topic)
    client.message_callback_add(userdata.subscribe_topic, on_wait)

################################################
## Publish functions
################################################

def send_uid(client, userdata, uid):
    payload = 'send_id:' + str(uid)
    print "Sending msg {} to {}".format(payload,userdata.publish_topic)
    client.publish(userdata.publish_topic, payload)

def send_leader(client,userdata, uid):
    payload = 'send_leader:' + str(uid)
    print "Sending msg {} to {}".format(payload,userdata.publish_topic)
    client.publish(userdata.publish_topic, payload)

def parse_msg(msg):
    msg_list = msg.split(':')
    message_name = msg_list[0]
    uid = int(msg_list[1])
    return message_name, uid

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

    myMQTT = MQTT_data(UID, upstream_UID)  #instance of your class

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

        # connect to broker
        client.connect(myMQTT.broker, myMQTT.port, keepalive=(myMQTT.keepalive))

        # subscribe to list of topics
        client.subscribe([(myMQTT.subscribe_topic, myMQTT.qos),
                          (myMQTT.will_topic, myMQTT.qos),
                          ])

        sleep(10)

        # initiate first publish of ID for leader election
        client.message_callback_add(myMQTT.subscribe_topic, on_active)
        send_uid(client, myMQTT, myMQTT.UID)
        myMQTT.active = True

        # main loop

        while(True):

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
            sleep(5)
            print "going into client.loop"
            client.loop(myMQTT.keepalive//2)
            print "client.loop timout"

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

if __name__ == "__main__":
    main()