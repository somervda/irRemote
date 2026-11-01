from ir_tx import Player
from sys import platform
import time
from machine import Pin

pin17 = Pin(17, Pin.OUT, value = 0)
# pin17.value(0)
# time.sleep(1)
# pin17.value(1)
# time.sleep(1)
# pin17.value(0)
ir = Player(pin17)
times= [9037, 4504, 506, 2224, 531, 4481, 531, 2199, 529]
ir.play(times)