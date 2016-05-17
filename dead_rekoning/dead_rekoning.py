import sys
from subprocess import Popen, PIPE
from binascii import hexlify
from grovepi import *

#####################################
# Global Constants
#####################################
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

######################################
# Ringo Communication
######################################
def signal_ringo(remote_code):
    # SEND_START, SEND_STOP, SEND_ONCE)
    print("Signaling ringo")
    Popen(("irsend", "SEND_ONCE", "Ringo", remote_code))
    blink_led()

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

def process_code(codes):
    print("Received codes: {}".format(hexlify(codes)))
    signal_ringo("KEY_9")

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
    Popen(["sudo", "/etc/init.d/lirc", "start"])
    p.wait()

def byte_to_hex(b):
    s = '0x'
    for byte in b:
        int(byte)

def ir_receive():
    # Receive NUM_BYTES_RCV bytes of data including the preamble on subprocess p

    binary = ''
    message = ''
    count = 0
    codes = bytearray()

    p = init_mode2()

    for line in iter(p.stdout.readline, b''): # b'' denotes a byte string literal
        #print line,
        line = processLine(line)
        if line == "Preamble2": #start keeping track of durations
            binary = ''
            message = ''
            count = 0
        try:
            binary += str(int(line))
        except:
            print line

        # space and duration = 2
        if len(binary) == 2:
            #message = str(int(binary, 2)) + message
            message = message + str(int(binary,2))
            binary = ''

        # 1 byte = 8 bits
        if len(message) == 8:
            if '2' in message:
                print "ERROR"
            else:
                codes.append(int(message, 2))
                print message, hexlify(codes), count +1
                count += 1
                message = ''
            if count == 4:
                break

    reset_lirc(p)
    blink_led()
    return codes

def blink_led():
    led = 4
    pinMode(led, "output")
    digitalWrite(led,1)
    time.sleep(1)
    digitalWrite(led,0)



def main():

    try:
        while True:
            codes = ir_receive()
            process_code(codes)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
