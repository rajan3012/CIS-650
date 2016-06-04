"""
Rickie Kerndt <rkerndt@cs.uoregon.edu>

Methods for sending/receiving communications from ringo
"""


import grovepi as gp
import subprocess

MY_KEY = "KEY_2"
PI_LED = 4

def blink_led():
    print("blinking my LED")
    led = 4
    gp.pinMode(led, "output")
    gp.digitalWrite(PI_LED,1)
    gp.time.sleep(1)
    gp.digitalWrite(PI_LED,0)

def signal_ringo():
    # SEND_START, SEND_STOP, SEND_ONCE)
    print("Signaling ringo")
    subprocess.Popen(("irsend", "SEND_ONCE", "Ringo", MY_KEY))

def is_button_on():
    """
    Reads button state when installed in position 3
    :return:  True when button is pressed
    """
    return gp.digitalRead(3) == gp.HIGH


def is_switch_on():
    """
    Reads switch state when installed in position 4
    :return:  True when switch is in the ON position
    """
    #return grovepi.digitalRead(4) == HIGH
    pass



