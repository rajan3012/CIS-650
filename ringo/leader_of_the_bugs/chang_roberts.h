
#ifndef __CHANG_ROBERTS_H__
#define __CHANG_ROBERTS_H__

#define MSG_SIZE 20
typedef unsigned char state_t;


enum states_t { s_active, s_deciding, s_passive, s_announce, s_waiting, s_working };

typedef struct Chang_Roberts {
    byte uid = 0x00;
    byte downstream_uid = 0x00;
    states_t state = s_active;
    bool is_active = false;
    byte leader = 0x00;
 } roberts_t;

typedef struct Message {
  byte src_uid;
  byte dst_uid;
  byte message_name;
  byte payload[MSG_SIZE - 3];
} __attribute__((pack)) message_t;

typedef struct Generic_Message {
  byte src_uid;
  byte dst_uid;
  byte message_name;
} generic_message_t;

struct Messasge_Names {
  byte send_id = 0x00;
  byte send_leader = 0x02;
  byte count_primes = 0x03;
} msg_names;



// function declartions
void decide(roberts_t *roberts, byte uid);
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
extern void ringo_receive(roberts_t* roberts, void (*handler) (void *userdata, byte *buf));
extern void on_topic(roberts_t *roberts, byte *buf);


#endif
