
#ifndef __CHANG_ROBERTS_H__
#define __CHANG_ROBERTS_H__

#define MSG_SIZE 10  // can not exceed IR_MAX_MSG_SIZE - HEADER_SIZE
#define MAX_RESEND_COUNT 10
typedef unsigned char state_t;


enum states_t { s_active, s_deciding, s_passive, s_announce, s_waiting, s_working };

typedef struct Chang_Roberts {
    byte uid = 0x00;
    byte downstream_uid = 0x00;
    states_t state = s_active;
    bool is_active = false;
    byte tenative_leader = 0x00;
    byte leader = 0x00;
    bool election_complete = false;
    unsigned int resend_count = 0;
 } roberts_t;

struct Message_Types {
  byte chang_roberts = 0x00;
  byte working = 0x01;
} msg_types;

struct Messasge_Names {
  byte send_id = 0x00;
  byte send_leader = 0x01;
} msg_names;

struct Message_Commands {
  byte count_primes = 0x00;
  byte move_forward = 0x01;
} msg_commands;

typedef struct Generic_Message {
  byte src_uid;
  byte dst_uid;
  byte message_type;
  byte payload[MSG_SIZE-3];
} __attribute__((pack)) gn_message_t;

typedef struct Chang_Roberts_Message {
  byte src_uid;
  byte dst_uid;
  byte message_type;
  byte message_name;
  byte payload[MSG_SIZE-4];
} __attribute__((pack)) cr_message_t;

typedef struct Working_Message {
  byte src_uid;
  byte dst_uid;
  byte message_type;
  byte command;
  byte payload[MSG_SIZE-4];
} __attribute__((pack)) wk_message_t;



// function declartions
extern void decide(roberts_t *roberts, byte uid);
extern void announce(roberts_t *roberts);
extern void working(roberts_t *roberts);
extern void active(roberts_t *roberts);
extern void passive(roberts_t *roberts);
extern void wait(roberts_t *roberts);
extern void send_uid(roberts_t *roberts, byte uid);
extern void send_leader(roberts_t *roberts, byte uid);
extern void send_primes(roberts_t *roberts, unsigned int lower_bound,  unsigned int count);
extern void count_primes(unsigned int lower_bound, unsigned int upper_bound);
extern void ringo_transmit(byte src_uid, byte dst_uid, byte *buf);
extern byte ringo_receive(byte my_uid, void *userdata, void (*handler) (void *userdata, byte *buf));
extern void on_topic(void *userdata, byte *buf);


#endif
