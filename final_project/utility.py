
from threading import Event
from sys import version_info

def interruptable_sleep(sleepy):
    """
    Using threading.Event to create an interruptable sleep routine
    Note: threading.wait() returns timeout period only the Python
    version 3.1 or higher.
    :param sleepy: seconds to sleep
    """
    nap = Event()
    if version_info > (3, 0):
        while sleepy > 0:
            sleepy -= nap.wait(sleepy)
            print('sleepiness {}'.format(sleepy))
    else:
        nap.wait(sleepy)

