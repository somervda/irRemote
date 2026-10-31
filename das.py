from machine import Pin
from ir_tx.raw import RAW
raw = RAW(Pin(17, Pin.OUT, value = 0))
raw.transmit(1, 2)  