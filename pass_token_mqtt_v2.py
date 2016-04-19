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

#############################################
## Get UID and upstram_UID from args
#############################################

if len(sys.argv) != 3:
	print 'ERROR\nusage: pass_token_mqtt.py <int: UID> <int: upstream UID>'
	sys.exit()

try:
    UID = int(sys.argv[1])
    upstream_UID = int(sys.argv[2]) 
except ValueError:
	print 'ERROR\nusage: pass_token_mqtt.py <int: UID > <int: upstream UID >'
	sys.exit()


#############################################
## MQTT settings
#############################################

broker      = 'blue0'
port        = 1883

# publish topics
send_token_topic = 'token/'+str(upstream_UID)

# subscribe topics
token_topic = 'token/'+str(UID)
will_topic = 'will/'

#quality of service
qos = 0 

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
    client.publish(send_token_topic, UID)

#Called when message received on will_topic
def on_will(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)

#Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    print('unfiltered message')


#############################################
## Connect to broker and subscribe to topics
#############################################
try:
    # create a client instance
    client = mqtt.Client(str(UID))

    # setup will for client
    will_message = "Dead UID: {}, upstream_UID: {} ".format(UID,upstream_UID)
    client.will_set(will_topic, will_message)

    # callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message 

    # callbacks for specific topics 
    client.message_callback_add(token_topic, on_token)
    client.message_callback_add(will_topic, on_will)

    # connect to broker 
    client.connect(broker, port, keepalive=30)

    # subscribe to list of topics
    client.subscribe([(token_topic, qos),
                      (will_topic, qos),
                      ])

    # initiate pub/sub
    if UID == 1:
        time.sleep(5)
        client.publish(send_token_topic, UID)

    # network loop
    client.loop_forever()

except (KeyboardInterrupt):
    print "Interrupt received"
except (RuntimeError):
    print "Runtime Error"
    client.disconnect()

