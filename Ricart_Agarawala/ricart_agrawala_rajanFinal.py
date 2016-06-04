'''
Name - Rajan Sawhney
UO ID - 951501267
CIS 650
Ricart-Agrawala
'''

import sys
import time
import paho.mqtt.client as mqtt

#############################################
## Global variables:
#############################################


# i = 1  #uid
# neighbours = [2,3] #neighbours list
# optimize:
'''
if the process wants the cs for the second time, it doesnt need to ask persmmision to all.
But only ask from process in pending queue. No need to ask all
If pending queue empty, you can access the cs
'''

#############################################
## MQTT settings
#############################################


class MQTT_data:
    def __init__(self, UID, in_neighbours):
        # self.States = Enum('active', 'decide', 'passive', 'announce', 'wait', 'working')
        self.UID = UID
        self.neighbours = in_neighbours
        self.broker = "white0"
        self.port = 1883
        # self.send_token_topic = 'token/' + str(''.join(in_neighbours)) #converting neighbours list to str
        self.will_topic = 'will/'
        # self.publish_topic = 'token/' + str(UID)
        # self.subscribe_topic = 'token/' + str(''.join(in_neighbours))
        self.will_message = 'DeadNode:'+ str(self.UID) + ":" + str(''.join(str(n)+':' for n in in_neighbours))
        self.qos = 2
        self.keepalive = 30
        self.connected = False
        self.wait_on_publish = False

        #### Specific to ricart agrawala
        self.request_topic = 'request/'
        self.permission_topic = 'permission/'
        self.counter = 0  # number of permissions i have
        self.pending = []  # intially empty
        self.requests = in_neighbours  # initially same as the neighbours
        self.privileged = False  # privileged true = in CS; false = not in CS
        self.req_stamp = 0  # 0 means no request
        self.clock = 1
        self.permission_from_list =[]
        self.will_sent = False


##############################################
## MQTT callbacks
##############################################

# Called when the broker responds to our connection request
def on_connect(client, userdata, flags, rc):
    if rc != 0:
        print("Connection failed. RC: " + str(rc))
    else:
        print("Connected successfully with result code RC: " + str(rc))
    time.sleep(3)


# Called when a published message has completed transmission to the broker
def on_publish(client, userdata, mid):
    # print("Message ID "+str(mid)+ " successfully published")
    pass


# Called when message received on will_topic
def on_will(client, userdata, msg):
    print "\n\n~~~~~~~~~~~~~~~~~~~"
    print "****Received message: " + str(msg.payload) + " on topic: " + msg.topic
    #n_list = [int(n) for n in parse_msg(msg.payload)]
    n_list = []

    msg_list = parse_msg(msg.payload)
    to_remove = int(msg_list[1])

    print 'node to remove=',to_remove
    '''
    for n in range(2,len(msg_list)-1):
        n_list.append(int(msg_list[n]))


    #n_list.remove(to_remove) #removing the dead id from list
    print "n_list is:",n_list
    print "**** Node-", to_remove, " died ****"

    # inform dead's neighbours
    for n in n_list:
        print 'sending remove to node-',n
        payload = 'remove:' + str(to_remove)
        client.publish(userdata.will_topic + str(n),payload)
    #userdata.neighbours.remove(int(msg.payload))  # remove dead neighbour
    '''
    '''
    if to_remove in userdata.requests:
        print "Before neighbours list:\t", userdata.neighbours
        userdata.neighbours.remove(to_remove)
        print "After neighbours list:\t", userdata.neighbours
    '''
    if to_remove in userdata.requests:
        print "Before requests list:\t", userdata.requests
        userdata.requests.remove(to_remove)
        print "After requests list:\t", userdata.requests
    if to_remove in userdata.pending:
        print "Before pending list:\t", userdata.pending
        userdata.pending.remove(to_remove)
        print "After pending list:\t", userdata.pending
    get_critical(client,userdata)

'''
def on_remove_dead_neighbour(client,userdata,msg):

    print "***Received message: " + str(msg.payload) + " on topic: " + msg.topic

    msg_name , to_remove = parse_msg(msg.payload)
    to_remove = int(to_remove)
    print 'node to remove=',to_remove
    if to_remove in userdata.requests:
        print "Before neighbours list:\t", userdata.neighbours
        userdata.neighbours.remove(to_remove)
        print "After neighbours list:\t", userdata.neighbours
    if to_remove in userdata.requests:
        print "Before requests list:\t", userdata.requests
        userdata.requests.remove(to_remove)
        print "After requests list:\t", userdata.requests
    if to_remove in userdata.pending:
        print "Before pending list:\t", userdata.pending
        userdata.pending.remove(to_remove)
        print "After pending list:\t", userdata.pending
    get_critical(client,userdata)

'''


# Called when a message has been received on a subscribed topic (unfiltered)
def on_message(client, userdata, msg):
    # print("Received message: "+str(msg.payload)+"on topic: "+msg.topic)
    # print('unfiltered message')
    pass


# on receiving request from j
def on_request(client, userdata, msg):  # if i receives request from j
    ''' msg contains: payload = 'request:' + str(n) + ':' + str(userdata.UID) + ":" +str(userdata.req_stamp)
    if not privileged and if no requests OR req time less that my req time and if same, j<i (process id)
    then grant permission'''

    print "\n\n~~~~~~~~~~~~~~~~~~~"
    print("****Received message: " + str(msg.payload) + "on topic: " + msg.topic)
    msg_name, my_neighbour, my_UID, my_req_stamp = parse_msg(msg.payload)

    i = userdata  # neighbour who gets request
    j = int(my_UID)
    j_time = int(my_req_stamp)
    time.sleep(2)
    print 'i_time =',userdata.clock
    print 'j_time =',j_time
    userdata.clock = max(userdata.clock, j_time + 1)
    # print("Request message received by node-",i.UID," by node-",my_UID)
    print 'new i_time =',userdata.clock
    if ((i.req_stamp == 0) or ((j_time, j) < (i.req_stamp, i.UID))):
        #payload = 'permission:' + str(j) + ':' + str(i.UID) + ':' + str(i.req_stamp)  # i gives permissipon to j
        payload = 'permission:' + str(i.UID)  # i gives permission to j and send it's own id
        # send_message(j, 'permission', i)  # pubslish this message - received by i. grant permission
        print('Giving permission to j=',j)
        print 'request list for node-'+ str(userdata.UID) +' = ' + str(userdata.requests)
        #print "payload is ->",payload
        client.publish(userdata.permission_topic + str(j), payload, userdata.qos, True)
        if(j not in userdata.requests):
            userdata.requests.append(j)
            if (i.req_stamp > 0): #requesting j
                # adding i to j's request list
                payload = 'request:' + str(j) + ':' + str(userdata.UID) + ':' + str(userdata.req_stamp)  # i requests j
                #print "payload is ->",payload
                client.publish(userdata.request_topic + str(j), payload, userdata.qos, True)
    else:
        if (j not in userdata.pending):
            print('adding ' + str(j) + ' to pending list of ' + str(userdata.UID))  # i in CS. adding j to pending list
            userdata.pending.append(j)  # add to pending list
        print 'pending list for node-{} is {}'.format(str(userdata.UID),str(userdata.pending))



# if permision from neighbour received
def on_permission(client, userdata, msg):
    print "\n\n~~~~~~~~~~~~~~~~~~~"
    print("****Received message: " + str(msg.payload) + " on topic: " + msg.topic)
    time.sleep(2)
    msg_name, permission_from = parse_msg(msg.payload)
    print 'permission list ->',userdata.permission_from_list
    print('Node-{} got persmission from node-{}'.format(userdata.UID, permission_from))

    if userdata.counter == 0 and len(userdata.permission_from_list) != 0 :
        userdata.counter = len(userdata.permission_from_list)
    print('Counter val:', userdata.counter)

    if permission_from not in userdata.permission_from_list:
        userdata.counter += 1
        userdata.permission_from_list.append(permission_from)
        print('New counter val:', userdata.counter)
    print 'request list ->',userdata.requests
    if userdata.counter == len(userdata.requests):  # if permission received from all neighbours in request list
        print 'all permissions received'
        userdata.counter = 0
        userdata.privileged = True  # can enter critical section
        perform_critical(client,userdata)
        userdata.permission_from_list =[]

################################################
## Publish functions
################################################

def send_uid(client, userdata, uid):
    payload = 'send_id:' + str(uid)
    print "Publishing msg {} on {}".format(payload, userdata.publish_topic)
    client.publish(userdata.publish_topic, payload, userdata.qos, True)
    userdata.wait_on_publish = True


def send_primes(client, userdata, lower_bound, count):
    payload = 'count_primes:' + str(lower_bound) + ':' + str(count)
    print "Publishing msg {} to {}".format(payload, userdata.publish_topic)
    client.publish(userdata.publish_topic, payload, userdata.qos, True)
    userdata.wait_on_publish = True


#############################################
##program functions
#############################################

# pending and request list is private list. every neighbour has it
def get_critical(client, userdata):
    time.sleep(2)
    print("in get_critical")
    print("Node-", userdata.UID, " trying to get into CS")

    userdata.req_stamp = userdata.clock
    userdata.clock += 1  # increasing clock
    print("Request list:", userdata.requests)
    if (len(userdata.requests) != 0):  # requests exists, ask all
        for n in userdata.requests:
            print "requesting node-", n
            # send_message(n, 'requests', clock,userdata.UID) #i - self UID
            payload = 'request:' + str(n) + ':' + str(userdata.UID) + ":" + str(userdata.req_stamp)  # clock - timestamp
            temp_r_topic = userdata.request_topic + str(n)
            #print "temp request topic = ", temp_r_topic
            print "payload",payload
            #client.publish(temp_r_topic, payload, userdata.qos, True)
            client.publish(temp_r_topic, payload)
            userdata.counter = 0
            time.sleep(1)
    else:
        print('Request list for ' + str(userdata.UID) + ' is empty. Perform Critical')
        time.sleep(1)
        userdata.privileged = True
        #print 'privilige value of node-'+str(userdata.UID)+' is:'+str(userdata.privileged)
        perform_critical(client,userdata)


def perform_critical(client, userdata):
    print "***************"
    print userdata.UID," - Doing work in Critical section........."
    userdata.privileged = False  # exiting CS
    time.sleep(8)
    print(str(userdata.UID) + " - Exiting from CS. Giving permission to all in pending")

    print "pending list = ",userdata.pending
    for p in userdata.pending:  # giving permission to all in pending
        print "sent permission to node-",p
        payload = 'permission:' + str(userdata.UID)
        #client.publish(userdata.permission_topic + str(p), payload, userdata.qos, True)
        client.publish(userdata.permission_topic + str(p), payload)
        time.sleep(2)
        # send_message(p,'permission',i)
    userdata.req_stamp = 0
    userdata.requests = userdata.pending
    userdata.pending = []  # empty pending
    print "pending list = ",userdata.pending
    print "***************"
    get_critical(client,userdata)
    #return


'''
while True:
    #do stuff outside of cs
    if cs_needed:
        get_critical()
        while (not privileged):
            #do other stuff while waiting
        perform_critical()
'''


##################################################
## Utility functions
##################################################
def parse_msg(msg):
    msg_list = msg.split(':')
    # message_name = msg_list[0]
    # uid = int(msg_list[1])
    return msg_list


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

    print "Found {} primes between {} and {} in {}".format(count, lower_bound, upper_bound, end - start)


def main():
    #############################################
    ## Get UID and upstream_UID from args
    #############################################
    ip_neighbours = []
    if len(sys.argv) < 3:
        print
        'ERROR\nusage: chain_roberts.py <int: UID> <int: upstream UID>'
        sys.exit()

    try:
        ip_UID = int(sys.argv[1])
        for i in range(2, len(sys.argv)):
            ip_neighbours.append(int(sys.argv[i]))
        print('Neighbour list=', ip_neighbours)

    except ValueError:
        print()
        'ERROR\nusage: ricart_agrawala.py <int: UID > <int: neighbours >'
        sys.exit()

    #############################################
    ## MQTT settings
    #############################################

    myMQTT = MQTT_data(ip_UID, ip_neighbours)  # copy mqtt settings here
    print("Node id=", myMQTT.UID, "\tand neighbours=", myMQTT.neighbours)
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
        temp_p_topic = myMQTT.permission_topic + str(myMQTT.UID)
        temp_r_topic = myMQTT.request_topic + str(myMQTT.UID)
        temp_w_topic = myMQTT.will_topic + str(myMQTT.UID)
        #print "temp request topic = ", temp_r_topic
        #print "temp permission topic = ", temp_p_topic
        #print "temp remove dead neighbours topic", temp_w_topic
        client.message_callback_add(myMQTT.will_topic, on_will)
        client.message_callback_add(temp_r_topic, on_request)  # request listens to topics with it's own id
        client.message_callback_add(temp_p_topic, on_permission)  # permission - same
        #client.message_callback_add(temp_w_topic, on_remove_dead_neighbour)
        # connect to broker
        client.connect(myMQTT.broker, myMQTT.port, keepalive=(myMQTT.keepalive))
        # spin wait on connect until we do anything else
        print "waiting to connect ..."

        if not myMQTT.connected:
            client.loop()
            #time.sleep(5)
        # print "Connected Successfully!"


        # subscribe to list of topics
        client.subscribe([(myMQTT.request_topic + str(myMQTT.UID), myMQTT.qos),
                          (myMQTT.will_topic + str(myMQTT.UID), myMQTT.qos),
                          (myMQTT.permission_topic + str(myMQTT.UID), myMQTT.qos),
                          (myMQTT.will_topic, myMQTT.qos)])


        # main loop
        '''
        while(True):
            get_critical(client, myMQTT)
            time.sleep(1)
            if (myMQTT.privileged):
                time.sleep(0.25)
                # do other stuff while waiting
                print("Permission obtained (main loop)")
                time.sleep(1)
                perform_critical(client, myMQTT)
            print("Not privileged")
            print("request list = ", myMQTT.requests)
            # network loop
            client.loop_forever()
            time.sleep(1)
        '''
        time.sleep(2)
        #while (True):
        #print('in loop')
        #do stuff outside of cs
        #if cs_needed:
        print 'Node-{}.privileged = ',myMQTT.privileged
        if(not myMQTT.privileged):
            print("Not priviliged")
            get_critical(client, myMQTT)
            print("request list = ", myMQTT.requests)

            '''
            print('request made')
            time.sleep(5)
            print 'Node-{}.privileged = ',myMQTT.privileged
            if (myMQTT.privileged):
                time.sleep(0.25)
                #do other stuff while waiting
                print("Permission obtained (main loop)")
                time.sleep(1)
                perform_critical(client,myMQTT)
            '''
            # network loop
            client.loop_forever()
            time.sleep(5)



    except (KeyboardInterrupt):
        print "Interrupt received"
    except (RuntimeError):
        print "Runtime Error"
        client.disconnect()


if __name__ == "__main__":
    main()