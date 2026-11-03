from ir_tx import Player
from sys import platform
import time
from machine import Pin
from keys import Keys
keys=Keys("keys.ir")
# print(keys.list())
times=keys.get("T 1")

pin17 = Pin(17, Pin.OUT, value = 0)
ir = Player(pin17,verbose=True)
ir.play(times)