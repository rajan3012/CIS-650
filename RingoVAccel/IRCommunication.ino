#include "RingoHardware.h"
#include "IRCommunication.h"

void ResetIR(short size) {
  RxIRRestart(size + HEADER_SIZE);
}

void SendIRMsg(byte sender, byte *msg, short size) {
  int i;
  irmsg[0] = 0x00;                  // all messages begin with 0x00
  irmsg[1] = sender;
  for (i = HEADER_SIZE; i < size + HEADER_SIZE; i++) {
    irmsg[i] = msg[i - HEADER_SIZE];
  }
  TxIR(irmsg, size + HEADER_SIZE);                 // actually transmit via any enabled IR sources
  RxIRRestart(size + HEADER_SIZE);
} //end TxIRNMsg()



