import time
from pyfirmata import Arduino, SERVO, util


### Arduino Info

port = '/dev/tty.usbmodem21401'       #port at which arduino is connected here
pins = [2, 3, 4, 5, 6, 7]      #list pins at which servos are connected here
board = Arduino(port)

hand_closed = 0
hand_open = 180

"""
Pin 2 - Middle - Open 160 Closed 0
Pin 3 - Index - Open 120 Closed 0
Pin 4 - Thumb - Open XX Closed 0
Pin 5 - Wrist - Keep at 20
Pin 6 - Pinky - Open 110 Closed 0
Pin 7 - Ring - Open 110 Closed 0
"""
for item in pins:
    board.digital[item].mode = SERVO

def rotate_servo(pin, angle):
    board.digital[pin].write(angle)
    time.sleep(0.015)
    time.sleep(1.015)

while True:
    rotate_servo(2, 0)
    # rotate_servo(2, hand_closed)
    # rotate_servo(2, hand_open)
    exit()
