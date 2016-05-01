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

// Callback wrapper
void roberts_rcv(void *userdata, message_t msg) {
  roberts_t &roberts = *((roberts_t*) userdata);
  on_topic(roberts, msg);
}

//# Use a single callback select by state, basically replace former call backs with elif blocks
void on_topic(roberts_t &roberts, message_t msg) {

    if (roberts.state == s_active) {
        //print "in active -- msg received: {}".format(msg.payload)
        byte uid = msg.payload[0];
        if (msg.message_name == msg_names.send_id) {
            decide(roberts, uid);
        }
        else if (msg.message_name == msg_names.send_leader) {
            send_leader(roberts, uid);
            working(roberts);
        }
    }
    else if (roberts.state == s_passive) {
        byte uid = msg.payload[0];
        if (msg.message_name == msg_names.send_leader) {
            roberts.leader = msg.payload[0];
            //print "Accepted {} as my leader".format(roberts.leader)
            send_leader(roberts, uid);
            working(roberts);
        }
        else if (msg.message_name == msg_names.send_id) {
            send_uid(roberts, uid);
        }
    }

    else if (roberts.state == s_waiting) {
        //print "in wait--- msg received: {}".format(msg.payload)
        if (msg.message_name == msg_names.send_leader) {
            //print "Leader announce has gone full circle"
            working(roberts);
        }
    }

    else if (roberts.state == s_working) {
    }
    else {
        //print "ERROR: in an undefined state!"
    }
}

//################################################
//## State Functions
//################################################
void decide(roberts_t &roberts, byte uid) {
    //print "State changed to decide"
    roberts.state = s_deciding;
    //print "uid={} roberts.UID={}".format(uid, roberts.UID)

    if (uid > roberts.uid) {
        send_uid(roberts, uid);
        passive(roberts);
        return;
    }
    else if (uid == roberts.uid) {
        //print "I, {},  am the leader".format(roberts.UID)
        announce(roberts);
        return;
    }

    //print "Going back to active"
    roberts.is_active = true;
    active(roberts);
}

void announce(roberts_t &roberts) {
    //print "State changed to announce"
    roberts.state = s_announce;
    roberts.leader = roberts.uid;
    send_leader(roberts, roberts.uid);
    wait(roberts);
}

void working(roberts_t &roberts) {
    //print "State changed to working"
    roberts.state = s_working;
    if (roberts.leader == roberts.uid) {
        //print "I'm the leader so let's get busy"
        //send_primes(roberts, 3, 1)
    }
}

void active(roberts_t &roberts) {
    //print "State changed to active:{}".format(roberts.active)
    roberts.state = s_active;

    // This allows a bad_leader attack. Better to remove it
    if (roberts.is_active == false) {
        send_uid(roberts, roberts.uid);
    }
}

void passive(roberts_t &roberts) {
    //print("State changed to passive")
    roberts.state = s_passive;
}


void wait(roberts_t &roberts) {
    //print("State changed to wait for round trip")
    roberts.state = s_waiting;
}


///################################################
///## Publish functions
///################################################

void send_uid(roberts_t &roberts, byte uid) {
    message_t msg;
    memset(&msg, '\0', sizeof(message_t));
    msg.src_uid = roberts.uid;
    msg.message_name = msg_names.send_id;
    msg.payload[0] = uid;
    //print "Publishing msg {} to {}".format(payload,roberts.publish_topic)
    ringo_transmit(msg);
}

void send_leader(roberts_t &roberts, byte uid) {
    message_t msg;
    memset(&msg, '\0', sizeof(message_t));
    msg.src_uid = roberts.uid;
    msg.message_name = msg_names.send_leader;
    msg.payload[0] = uid;
    //print "Publishing msg {} to {}".format(payload,roberts.publish_topic)
    ringo_transmit(msg);
}

void send_primes(roberts_t &roberts, unsigned int lower_bound,  unsigned int count) {
    message_t msg;
    memset(&msg, '\0', sizeof(message_t));
    msg.src_uid = roberts.uid;
    msg.message_name = msg_names.count_primes;
    // encode lower_bound and count into payload

    ringo_transmit(msg); 
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
roberts_t roberts;
memset(&roberts, '\0', sizeof(roberts_t);

// guess have to hard code uid's
roberts.uid = 0x00;
roberts.downstream_uid = 0x00;


// Main loop, ringo_receive will call handlers which handles state changes
// required for leader election.
// If any action is required within the main loop, then place that code
// within the appropraite else-if block for the current state.
void loop() {
  

    // else-if blocks for each state
    if (rogers.state == s_active) {
        // active state main loop code goes here
    }
    else if (rogers.state == s_announce) {
        // announce state main loop code goes here
    }
    else if (rogers.state == s_deciding) {
        // decide state main loop code goes here
    }
    else if (rogers.state == s_passive) {
        // passive state main loop code goes here
    }
    else if (rogers.state == s_waiting) {
        // waiting state main loop code goes here
    }
    else if (rogers.state == s_working) {
        // working state main loop code goes here
    }
    else {
    }
      
    ringo_receive(rogers.uid, &roberts_rcv);
    
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
}

void ringo_transmit(message_t &msg) {
    // Simple MSG_SIZE message sending exampled
    ResetIR(MSG_SIZE);
    
    //OnEyes(0,50,50); // use eye color to indicate what the Ringo is doing, or state, etc. (this is just a placeholder)
  
    // Send a message to device with ID targetID 
    SendIRMsg(msg.src_uid, msg.dst_uid, msg, MSG_SIZE);
  
    // To receive above message on ID 0x02 Ringo, issue ReceiveIRMsg(senderID, 0x02, msg, MSG_SIZE);
    ResetIR(MSG_SIZE); // Important!
    delay(random(100,150));          // delay 1 second (1000 milliseconds = 1 second)
}

void ringo_receive(byte my_uid, void (*handler) (void *userdata, message_t msg) {
    byte sender;
    bool done = 0;
    message_t msg;
    memset(&msg, '\0', sizeof(message_t));
    
    // put your code here inside the loop() function.  Here's a quick example that makes the eyes alternate colors....
    //if (!done) OnEyes(50,0,0);      // you can remove this stuff and put your own code here
    if (ReceiveIRMsg(sender, my_uid, msg, MSG_SIZE)) {
        Serial.print(my_uid, HEX);
        Serial.print(" received IR message from "); Serial.println(sender, HEX);
        // Print just the payload
        Serial.println(msg.src_uid,HEX);
        Serial.println(msg.dst_uid,HEX);
        ResetIR(MSG_SIZE);
     
        if (msg.dst_uid == my_uid) {
          OnEyes(0,200,0);
          PlayChirp(NOTE_FS3,40); delay(200); PlayChirp(NOTE_D4, 40); delay(200);
          OffEyes();
          handler(userdata, msg)
          done = 1;
        }
    }
    delay(random(50,150));

}

