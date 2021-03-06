#!/usr/bin/env python2
"""
precursor commands:
sudo killall mode2
sudo /etc/init.d/lirc stop
mode2 -d /dev/lirc0

mode2 output:
space xxx
pulse yyy

For IR communication to Ringo robot should receive 4 bytes (32 bits)
1st byte == all 0's
2nd byte == all 1's
3rd,4th == message
"""

from subprocess import Popen, PIPE

# PREAMBLE
beginSend_firstNum = 9000
beginSend_secondNum = 4500
# DATA
data_zeroNum = 600
data_oneNum = 1600
# JUNK
garbage = 20000

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

def main():
    binary = ''
    message = ''
    count = 0

    #Popen(["sudo", "killall", "mode2"])
    #Popen(["sudo", "/etc/init.d/lirc", "stop"])
    p = Popen(["mode2","-d", "/dev/lirc0"], stdout=PIPE,bufsize=1)
    with p.stdout:
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
                message = str(int(binary, 2)) + message
                binary = ''

            # 1 byte = 8 bits
            if len(message) == 8:
                if '2' in message: 
                    print "ERROR"
                else:
                    count += 1
                    print message, hex(int(message, 2)), count
                    message = ''
    p.wait()

if __name__ == "__main__":
    main()
