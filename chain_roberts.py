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
        self.token_topic = 'token/' + str(UID)
        self.will_message = "Dead UID: {}, upstream_UID: {} ".format(UID, upstream_UID)
        self.qos = 0
        self.state = States.active
        self.active = False

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
        client = mqtt.Client(str(myMQTT.UID))

        # setup will for client

        client.will_set(myMQTT.will_topic, myMQTT.will_message)

        # setup userdata for clien
        client.user_data_set(myMQTT)

        # callbacks
        client.on_connect = on_connect
        client.on_publish = on_publish
        client.on_message = on_message

        # callbacks for specific topics
        client.message_callback_add(myMQTT.token_topic, on_token)
        client.message_callback_add(myMQTT.will_topic, on_will)

        # connect to broker
        client.connect(myMQTT.broker, myMQTT.port, keepalive=30)

        # subscribe to list of topics
        client.subscribe([(myMQTT.token_topic, myMQTT.qos),
                          (myMQTT.will_topic, myMQTT.qos),
                          ])

        # initiate pub/sub
        if UID == 1:
            time.sleep(5)
            client.publish(myMQTT.send_token_topic, myMQTT.UID)

        # network loop
        client.loop_forever()

    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()

if __name__ == "__main__":
    main()