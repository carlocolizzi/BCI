from pylsl import StreamInlet, resolve_stream
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib import style
from collections import deque
import os
import random
import tensorflow as tf
from pyfirmata import Arduino, SERVO, util


### Arduino Info

port = ''       #port at which arduino is connected here
pins = [9, 10, 11, 12, 13, 14]      #list pins at which servos are connected here
board = Arduino(port)

hand_closed = 0
hand_open = 90

for item in pins:
    board.digital[item].mode = SERVO

def rotate_servo(pin, angle):
    board.digital[pin].write(angle)
    time.sleep(0.015)

### ML code

MODEL_NAME = ""  # your model path here. 

model = tf.keras.models.load_model(MODEL_NAME)
reshape = (-1, 16, 60)
model.predict( np.zeros((32,16,60)).reshape(reshape) )

ACTION = 'left' # THIS IS THE ACTION YOU'RE THINKING 

FFT_MAX_HZ = 60

HM_SECONDS = 10  # this is approximate. Not 100%. do not depend on this.
TOTAL_ITERS = HM_SECONDS*25  # ~25 iters/sec
BOX_MOVE = "model"  # random or model

last_print = time.time()
fps_counter = deque(maxlen=150)

# first resolve an EEG stream on the lab network
print("looking for an EEG stream...")
streams = resolve_stream('type', 'EEG')
# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

WIDTH = 800
HEIGHT = 800
SQ_SIZE = 50
MOVE_SPEED = 1

square = {'x1': int(int(WIDTH)/2-int(SQ_SIZE/2)), 
          'x2': int(int(WIDTH)/2+int(SQ_SIZE/2)),
          'y1': int(int(HEIGHT)/2-int(SQ_SIZE/2)),
          'y2': int(int(HEIGHT)/2+int(SQ_SIZE/2))}


box = np.ones((square['y2']-square['y1'], square['x2']-square['x1'], 3)) * np.random.uniform(size=(3,))
horizontal_line = np.ones((HEIGHT, 10, 3)) * np.random.uniform(size=(3,))
vertical_line = np.ones((10, WIDTH, 3)) * np.random.uniform(size=(3,))

total = 0
left = 0
right = 0
none = 0
correct = 0 

channel_datas = []

for i in range(TOTAL_ITERS):  # how many iterations. Eventually this would be a while True
    channel_data = []
    for i in range(16): # each of the 16 channels here
        sample, timestamp = inlet.pull_sample()
        channel_data.append(sample[:FFT_MAX_HZ])

    fps_counter.append(time.time() - last_print)
    last_print = time.time()
    cur_raw_hz = 1/(sum(fps_counter)/len(fps_counter))
    print(cur_raw_hz)

    network_input = np.array(channel_data).reshape(reshape)
    out = model.predict(network_input)
    print(out[0])

    if BOX_MOVE == "model":
        choice = np.argmax(out)
        if choice == 0:         #left
            for item in pins:
                rotate_servo(item, hand_closed)

            left += 1

        elif choice == 2:       #right
            for item in pins:
                rotate_servo(item, hand_open)
            
            right += 1

        else:
            none += 1

    total += 1


    channel_datas.append(channel_data)


datadir = "data"
if not os.path.exists(datadir):
    os.mkdir(datadir)

actiondir = f"{datadir}/{ACTION}"
if not os.path.exists(actiondir):
    os.mkdir(actiondir)

print(len(channel_datas))

print(f"saving {ACTION} data...")
np.save(os.path.join(actiondir, f"{int(time.time())}.npy"), np.array(channel_datas))
print("done.")

for action in ['left', 'right', 'none']:
    #print(f"{action}:{len(os.listdir(f'data/{action}'))}")
    print(action, sum(os.path.getsize(f'data/{action}/{f}') for f in os.listdir(f'data/{action}'))/1_000_000, "MB")

print(ACTION, correct/total)
print(f"left: {left/total}, right: {right/total}, none: {none/total}")

with open("accuracies.csv", "a") as f:
    f.write(f"{int(time.time())},{ACTION},{correct/total},{MODEL_NAME},{left/total},{right/total},{none/total}\n")
