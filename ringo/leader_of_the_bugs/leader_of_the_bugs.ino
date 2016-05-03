#include "RingoHardware.h"
#include "FunStuff.h"
#include "IRCommunication.h"
#include <math.h>
#include <string.h>
#include "chang_roberts.h"


////////////////////////////////////////////////////////
// port of chang_roberts.py
///////////////////////////////////////////////////////



//##############################################
//## receive callbacks
//##############################################


//# Use a single callback select by state, basically replace former call backs with elif blocks
void on_topic(void *userdata, byte *buf) {

    roberts_t *roberts = (roberts_t*) userdata;
    gn_message_t *gmsg = (gn_message_t*) buf;

    // check whether this message is for me
    if ((gmsg->dst_uid != roberts->uid) && (gmsg->dst_uid != IR_BROADCAST)) {
      return;
    }

    Serial.print("Message = ");
    Serial.print(" src_uid: ");
    Serial.print(gmsg->src_uid,HEX);
    Serial.print(", dst_uid: ");
    Serial.print(gmsg->dst_uid,HEX);
    Serial.print(", message_type: ");
    Serial.println(gmsg->message_type,HEX);

    if ((roberts->state != s_working) && (gmsg->message_type != msg_types.working)) {
      cr_message_t *msg = (cr_message_t*) buf;
      
        if (roberts->state == s_active) {
            Serial.print("in active");
            byte uid = msg->payload[0];
            if (msg->message_name == msg_names.send_id) {
                Serial.print(" rcvd uid=");
                Serial.println(uid,HEX);
                decide(roberts, uid);
            }
            else if (msg->message_name == msg_names.send_leader) {
                Serial.print(" rcvd leader uid=");
                Serial.println(uid,HEX);
                send_leader(roberts, uid);
                working(roberts);
            }
        }
        else if (roberts->state == s_passive) {
            Serial.print("in passive");
            byte uid = msg->payload[0];
            if (msg->message_name == msg_names.send_leader) {
                Serial.print(" rcvd leader uid=");
                Serial.println(uid,HEX);
                roberts->leader = uid;
                send_leader(roberts, uid);
                working(roberts);
            }
            else if (msg->message_name == msg_names.send_id) {
                Serial.print(" rcvd uid=");
                Serial.println(uid,HEX);
                send_uid(roberts, uid);
            }
        }
        else if (roberts->state == s_waiting) {
            Serial.println("in waiting, I am the Leader");
            if (msg->message_name == msg_names.send_leader) {
                working(roberts);
            }
        }
    }
    else if ((roberts->state == s_working) && (gmsg->message_type == msg_types.working)) {
        Serial.println("in working");
        wk_message_t *msg = (wk_message_t*) buf;
      // TODO: add movement
    }
    else {
        // probably an error in targeted address from all the noise so just ignore
    }
}

//################################################
//## State Functions
//################################################
void decide(roberts_t *roberts, byte uid) {
    //print "State changed to decide"
    roberts->state = s_deciding;
    //print "uid={} roberts.UID={}".format(uid, roberts.UID)

    if (uid > roberts->uid) {
        send_uid(roberts, uid);
        passive(roberts);
        return;
    }
    else if (uid == roberts->uid) {
        //print "I, {},  am the leader".format(roberts.UID)
        announce(roberts);
        return;
    }

    //print "Going back to active"
    roberts->is_active = true;
    active(roberts);
}

void announce(roberts_t *roberts) {
    //print "State changed to announce"
    roberts->state = s_announce;
    roberts->leader = roberts->uid;
    send_leader(roberts, roberts->uid);
    wait(roberts);
}

void working(roberts_t *roberts) {
    //print "State changed to working"
    roberts->state = s_working;
    if (roberts->leader == roberts->uid) {
        //print "I'm the leader so let's get busy"
        //send_primes(roberts, 3, 1)
    }
}

void active(roberts_t *roberts) {
    //print "State changed to active:{}".format(roberts.active)
    roberts->state = s_active;

    if (roberts->is_active == false) {
        roberts->state = s_active;
        roberts->is_active = true;
        send_uid(roberts, roberts->uid);
    }
}

void passive(roberts_t *roberts) {
    //print("State changed to passive")
    roberts->state = s_passive;
}

void wait(roberts_t *roberts) {
    //print("State changed to wait for round trip")
    roberts->state = s_waiting;
}


///################################################
///## Publish functions
///################################################

void send_uid(roberts_t *roberts, byte uid) {
    Serial.print("Sending uid: ");
    Serial.println(uid, HEX);
    cr_message_t *msg = (cr_message_t*) calloc(1, sizeof(cr_message_t));
    msg->src_uid = roberts->uid;
    msg->message_name = msg_names.send_id;
    msg->payload[0] = uid;
    //print "Publishing msg {} to {}".format(payload,roberts.publish_topic)
    IR_transmit(roberts->uid, roberts->downstream_uid, (byte*) msg, MSG_SIZE);
    free(msg);
}

void send_leader(roberts_t *roberts, byte uid) {
    Serial.print("Sending leader: ");
    Serial.println(uid, HEX);
    cr_message_t *msg = (cr_message_t*) calloc(1, sizeof(cr_message_t));
    msg->src_uid = roberts->uid;
    msg->message_name = msg_names.send_leader;
    msg->payload[0] = uid;
    //print "Publishing msg {} to {}".format(payload,roberts.publish_topic)
    IR_transmit(roberts->uid, roberts->downstream_uid, (byte*) msg, MSG_SIZE);
    free(msg);
}

void send_primes(roberts_t *roberts, unsigned int lower_bound,  unsigned int count) {
    wk_message_t *msg = (wk_message_t*) calloc(1, sizeof(wk_message_t));
    msg->src_uid = roberts->uid;
    msg->command = msg_commands.count_primes;
    // encode lower_bound and count into payload

    IR_transmit( roberts->uid, roberts->downstream_uid, (byte*) msg, MSG_SIZE);
    free(msg);
}

//##################################################
//## Work functions
//##################################################

void count_primes(unsigned int lower_bound, unsigned int upper_bound) {

    unsigned int count = 0;

    for (unsigned int n = lower_bound; n < upper_bound; ++n) {
        unsigned int upper = (unsigned int) ceil(sqrt(n));
        for (unsigned int i; i < upper; ++i) {
            if (n % i != 0) {
                break;
            count += 1;
            }
        }
    }

    //print "Found {} primes between {} and {} in {}".format(count, lower_bound, upper_bound, end-start)
}

//#############################################
//## global variables
//#############################################
roberts_t *roberts = NULL;
byte *buf = NULL;

// Main loop, ringo_receive will call handlers which handles state changes
// required for leader election.
// If any action is required within the main loop, then place that code
// within the appropraite else-if block for the current state.
void loop() {
  

    // else-if blocks for each state
    if (roberts->state == s_active) {
        // active state main loop code goes here
        OnEyes(255,0,0); // red
        if (roberts->is_active == false) {
          active(roberts);
        }
    }
    else if (roberts->state == s_announce) {
        // announce state main loop code goes here
        OnEyes(255,128,0); // orange
    }
    else if (roberts->state == s_deciding) {
        // decide state main loop code goes here
        OnEyes(127,0,255); // purple
    }
    else if (roberts->state == s_passive) {
        // passive state main loop code goes here
        OnEyes(255,255,0); // yellow
    }
    else if (roberts->state == s_waiting) {
        // waiting state main loop code goes here
        OnEyes(0,255,255); // cyan
    }
    else if (roberts->state == s_working) {
        // working state main loop code goes here
        OnEyes(0,255,0); // green
    }
    else {
    }
      
    byte sender = IR_receive(roberts->uid, roberts, &on_topic, buf, MSG_SIZE);

    // make some noise if we received and processed a message
    if (sender != 0) {
        Serial.print(roberts->uid, HEX);
        Serial.print(" received IR message from "); Serial.println(sender, HEX);
        OnEyes(0,200,0);
        PlayChirp(NOTE_FS3,40); delay(200); PlayChirp(NOTE_D4, 40); delay(200);
        OffEyes();
    }
}


void setup() {
  HardwareBegin();        //initialize Ringo's brain to work with his circuitry
  PlayStartChirp();       //Play startup chirp and blink eyes
  SwitchMotorsToSerial(); //Call "SwitchMotorsToSerial()" before using Serial.print functions as motors & serial share a line

  // This should be called if planning to send 2-byte (payload) messages
  ResetIR(MSG_SIZE);

  Serial.begin(9600);
  randomSeed(analogRead(0));
  RestartTimer();

  // Initialize global data structures
  buf = (byte*) calloc(MSG_SIZE, sizeof(byte));
  roberts = (roberts_t*) calloc(1,sizeof(roberts_t));
  roberts->uid = 0x05;
  roberts->downstream_uid = 0x06;
  roberts->state = s_active;
  roberts->is_active = false;
}

void ringo_transmit(byte src_uid, byte dst_uid, byte *buf) {

    // turn off lights for Transmitting
    OnEyes(0,0,0);
    
    // Simple MSG_SIZE message sending exampled
    ResetIR(MSG_SIZE);
      
    // Send a message to device with ID targetID 
    SendIRMsg(src_uid, dst_uid, buf, MSG_SIZE);
  
    // To receive above message on ID 0x02 Ringo, issue ReceiveIRMsg(senderID, 0x02, msg, MSG_SIZE);
    ResetIR(MSG_SIZE); // Important!
    delay(random(100,150));          // delay 1 second (1000 milliseconds = 1 second)
}

byte ringo_receive(byte my_uid, void *userdata, void (*handler) (void *userdata, byte *buf)) {
    byte *buf = (byte*) calloc(MSG_SIZE, sizeof(byte));
    byte sender;

    // turn off lights for Receiving
    OnEyes(0,0,0);
    
    // put your code here inside the loop() function.  Here's a quick example that makes the eyes alternate colors....
    //if (!done) OnEyes(50,0,0);      // you can remove this stuff and put your own code here
    if (ReceiveIRMsg(sender, my_uid, buf, MSG_SIZE)) {
        Serial.print(my_uid, HEX);
        Serial.print(" received IR message from "); Serial.println(sender, HEX);
        // Print just the payload
        
        ResetIR(MSG_SIZE);
     
        OnEyes(0,200,0);
        PlayChirp(NOTE_FS3,40); delay(200); PlayChirp(NOTE_D4, 40); delay(200);
        OffEyes();
        handler(userdata, buf);
    }
    free(buf);
    return sender;
}

