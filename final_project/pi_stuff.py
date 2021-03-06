"""
Rickie Kerndt <rkerndt@cs.uoregon.edu>

Methods for sending/receiving communications from ringo
"""
import sys
from subprocess import Popen, PIPE
from binascii import hexlify
import grovepi as gp
from utility import *

PI_LED = 4
PI_HIGH = 1
PI_LOW = 0
PI_GO = 0
PI_DONE = 1
PI_ACK = 2

"""
bit ordering for expected key code from ringo
              msb -- lsb
KEY_0: 0x00ff6897 -- 0x00ff16d9
KEY_1: 0x00ff30cf -- 0x00ff0cf3
KEY_2: 0x00ff18e7 -- 0x00ff817e
"""

RINGO_CODES = [ None,
                ["KEY_9", bytearray([0x00,0xff,0x68,0x97]), "KEY_7"],
                ["KEY_4", bytearray([0x00,0xff,0x30,0xcf]), "KEY_5"],
                ["KEY_6", bytearray([0x00,0xff,0x18,0xe7]), "KEY_8"]
              ]

# PREAMBLE
beginSend_firstNum = 9000
beginSend_secondNum = 4500

# DATA
data_zeroNum = 600
data_oneNum = 1600
# JUNK
garbage = 20000

# Total number of bytes to receive
NUM_BYTES_RCV = 4

def receive_ringo(byte_code):

    return ir_receive() == byte_code

def is_button_on(want=True):
    """
    Reads button state when installed in position 3
    :return:  True when button is pressed
    """
    return gp.digitalRead(3) == PI_HIGH

def is_switch_on():
    """
    Reads switch state when installed in position 4
    :return:  True when switch is in the ON position
    """
    return gp.digitalRead(4) == PI_HIGH

def signal_ringo(remote_code):
    # SEND_START, SEND_STOP, SEND_ONCE)
    print("Signaling ringo .")
    for i in range(2):
        on_led()
        Popen(("irsend", "SEND_ONCE", "Ringo", remote_code))
        interruptable_sleep(1)
        off_led()

def processLine(line):
    reading = line.split()
    reading[1] = int(reading[1])
    if reading[0] == "space":
        return durToByte(reading[1])
    elif reading[0] == "pulse":
        return durToByte(reading[1])
    else:
        sys.exit()

def durToByte(duration):
    dct = {}
    dct["Preamble1"] = abs(beginSend_firstNum  - duration)
    dct["Preamble2"] = abs(beginSend_secondNum  - duration)
    dct["0"] = abs(data_zeroNum - duration)
    dct["1"] = abs(data_oneNum - duration)
    dct["garbage"] = abs(garbage- duration)
    return min(dct, key=dct.get)

def init_mode2():
    p = Popen(["sudo", "killall", "mode2"])
    p.wait()
    p = Popen(["sudo", "/etc/init.d/lirc", "stop"])
    p.wait()
    p = Popen(["mode2","-d", "/dev/lirc0"], stdout=PIPE,bufsize=1)
    return p

def reset_lirc(p):
    p.terminate()
    p.wait()
    p = Popen(["sudo", "killall", "mode2"])
    p.wait()
    p = Popen(["sudo", "/etc/init.d/lirc", "start"])
    p.wait()
    print("lirc start return code={}".format(p.returncode))


def ir_receive():
    # Receive NUM_BYTES_RCV bytes of data including the preamble on subprocess p

    binary = ''
    message = ''
    count = 0
    codes = bytearray()

    p = init_mode2()

    for line in iter(p.stdout.readline, b''): # b'' denotes a byte string literal
        line = processLine(line)
        if line == "Preamble2": #start keeping track of durations
            binary = ''
            message = ''
            count = 0
        try:
            binary += str(int(line))
        except:
            pass

        # space and duration = 2
        if len(binary) == 2:
            # select bit order here, remote and pi differ
            #message = str(int(binary, 2)) + message
            message = message + str(int(binary,2))
            binary = ''

        # 1 byte = 8 bits
        if len(message) == 8:
            if '2' in message:
                print "ERROR"
            else:
                on_led()
                codes.append(int(message, 2))
                count += 1
                message = ''
                off_led()
            if count == 4:
                break

    print('received {}'.format(hexlify(codes)))
    reset_lirc(p)
    return codes

def on_led():
    gp.pinMode(PI_LED, "output")
    gp.digitalWrite(PI_LED,1)

def off_led():
    gp.pinMode(PI_LED, "output")
    gp.digitalWrite(PI_LED,0)

def blink_led(seconds):
    on_led()
    interruptable_sleep(seconds)
    off_led()



