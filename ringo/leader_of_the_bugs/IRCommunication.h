/* Simple generic message communication interface. Each message has size+3 bytes. 
 *  The first three bytes are 0x00, recipient ID (1 byte), sender ID (1 byte). 
 */
#ifndef __IRCommunication_H
#define __IRCommunication_H

#define HEADER_SIZE 3
#define IR_BROADCAST 0xFF
#define IR_MAX_MSG_SIZE 20 // max in RingoHardware is 20, including header

byte irmsg[IR_MAX_MSG_SIZE];

void ResetIR(short size);

// Broadcast messages should have 0 as the recipient

void SendIRMsg(byte sender, byte recipient, byte *msg, short size);

int ReceiveIRMsg(byte &sender, byte recipient, byte *msg, short size);

int IR_transmit(byte src_uid, byte dst_uid, byte *msg, unsigned int size);

byte IR_receive(byte my_uid, void *userdata, void (*handler) (void *userdata, byte *msg), byte* msg, unsigned int size);

#endif
