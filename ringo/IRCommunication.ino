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
    if (IRBytes[1] != recipient) {
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

