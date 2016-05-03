#include "RingoHardware.h"
#include "IRCommunication.h"

void ResetIR(short size) {
  RxIRRestart(size + HEADER_SIZE);
}

void SendIRMsg(byte sender, byte recipient, byte *msg, short size) {
  int i;
  irmsg[0] = 0x00;                  // all messages begin with 0x00
  irmsg[1] = recipient;
  irmsg[2] = sender;
  for (i = HEADER_SIZE; i < size + HEADER_SIZE; i++) {
    irmsg[i] = msg[i - HEADER_SIZE];
  }
  TxIR(irmsg, size + HEADER_SIZE);                 // actually transmit via any enabled IR sources
  RxIRRestart(size + HEADER_SIZE);
} //end TxIRNMsg()

int ReceiveIRMsg(byte &sender, byte recipient, byte *msg, short size) {
  int i;
  if (!IsIRDone()) {      // will return "0" if no IR packet has been received
    RxIRRestart(size + HEADER_SIZE);
    return 0;
  } else {
    RxIRStop();         //stop the receiving function
    // The first byte is always 0x00
    // First, check that recipient matches what is expected, that is always the second byte
    if ((IRBytes[1] != recipient) || (IRBytes[1] != IR_BROADCAST)) {
      RxIRRestart(size + HEADER_SIZE);
      return 0; // the message is not for me
    }
   
    sender = IRBytes[2];
    for (i = HEADER_SIZE; i < size + HEADER_SIZE; i++) {
      msg[i - HEADER_SIZE] = IRBytes[i];
    }

    for (i = 0; i < size + HEADER_SIZE; i++)
      IRBytes[i] = 0;

    RxIRRestart(size + HEADER_SIZE);          //restart the IR Rx function before returning
  } // end if(!IsIRDone()) else
  return 1;
} // end ReceiveIRMsg


int IR_transmit(byte src_uid, byte dst_uid, byte *msg, unsigned int size) {

    // turn off lights for transmitting
    OnEyes(0,0,0);
    delay(100);
    
    ResetIR(size);
      
    // Send a message to device with ID targetID 
    irmsg[0] = 0x00;                  // all messages begin with 0x00
    irmsg[1] = dst_uid;
    irmsg[2] = src_uid;
    for (int i = HEADER_SIZE; i < size + HEADER_SIZE; i++) {
      irmsg[i] = msg[i - HEADER_SIZE];
    }
    TxIR(irmsg, size + HEADER_SIZE);                 // actually transmit via any enabled IR sources
    RxIRRestart(size + HEADER_SIZE);

    // To receive above message on ID 0x02 Ringo, issue ReceiveIRMsg(senderID, 0x02, msg, MSG_SIZE);
    ResetIR(size); // Important!
    delay(random(100,150));          // delay 1 second (1000 milliseconds = 1 second)
}

byte IR_receive(byte my_uid, void *userdata, void (*handler) (void *userdata, byte *msg), byte* msg, unsigned int size) {
    byte sender = 0;

    // turn off lights for receiving
    OnEyes(0,0,0);
    delay(100);

    if (!IsIRDone()) {      // will return "0" if no IR packet has been received
      RxIRRestart(size + HEADER_SIZE);
      Serial.println("IR_receive gots nothing to report");
      return 0;
    }
    else {
      RxIRStop();         //stop the receiving function

      Serial.print("IR_receive gots message from ");
      Serial.println(IRBytes[1], HEX);
      
      // The first byte is always 0x00
      // First, check that recipient matches what is expected, that is always the second byte
      if ((IRBytes[1] != my_uid) || (IRBytes[1] != IR_BROADCAST)) {
        RxIRRestart(size + HEADER_SIZE);
        return 0; // the message is not for me
      }
     
      sender = IRBytes[2];
      for (int i = HEADER_SIZE; i < size + HEADER_SIZE; i++) {
        msg[i - HEADER_SIZE] = IRBytes[i];
      }
  
      for (int i = 0; i < size + HEADER_SIZE; i++)
        IRBytes[i] = 0;
  
      RxIRRestart(size + HEADER_SIZE);          //restart the IR Rx function before returning

      
      handler(userdata, msg);
      return sender;
    }
}


