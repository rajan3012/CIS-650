#include "RingoHardware.h"
#include "FunStuff.h"
#include "IRCommunication.h"


#define MSG_SIZE 2
byte msg[MSG_SIZE];

byte myID = 0x01;
byte otherID = 0x02;

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

void sendExample() {
  // Simple 2-byte message sending exampled
  ResetIR(MSG_SIZE);
  byte targetID = otherID;   // ID of message target

  // Message payload
  msg[0] = 0xA0;
  msg[1] = 0xA4;
  
  //OnEyes(0,50,50); // use eye color to indicate what the Ringo is doing, or state, etc. (this is just a placeholder)

  // Send a message to device with ID targetID 
  SendIRMsg(myID, targetID, msg, MSG_SIZE);

  // To receive above message on ID 0x02 Ringo, issue ReceiveIRMsg(senderID, 0x02, msg, MSG_SIZE);
  ResetIR(MSG_SIZE); // Important!
  delay(random(100,150));          // delay 1 second (1000 milliseconds = 1 second)
}

void receiveExample() {
  byte sender;
  bool done = 0;
  // put your code here inside the loop() function.  Here's a quick example that makes the eyes alternate colors....
  //if (!done) OnEyes(50,0,0);      // you can remove this stuff and put your own code here
  if (ReceiveIRMsg(sender, myID, msg, MSG_SIZE)) {
    Serial.print(myID, HEX);
    Serial.print(" received IR message from "); Serial.println(sender, HEX);
    // Print just the payload
    Serial.println(msg[0],HEX);
    Serial.println(msg[1],HEX);
    if (msg[0] == 0xA0) {
      OnEyes(0,200,0);
      PlayChirp(NOTE_FS3,40); delay(200); PlayChirp(NOTE_D4, 40); delay(200);
      OffEyes();
      done = 1;
    }
    ResetIR(MSG_SIZE);
  }
  
  delay(random(50,150));
}

void loop(){ 

  // Uncomment either send or receive before upload to two different devices for testing.
  sendExample();
  receiveExample();
}

