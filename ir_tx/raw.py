# RAW IR timing transmiter
# Will take a list of timings , load them to the ir transmit array
#  and transmit the raw timings using the specified carrer frequency

# Author: Peter Hinch
# Copyright Peter Hinch 2020-2022 Released under the MIT license
# Updated by David Somerville

from micropython import const
from ir_tx import IR, STOP



class RAW(IR):

    def __init__(self, pin, freq=38000, verbose=True):  # Default to 38KHz 
        super().__init__(pin, freq, 68, 33, verbose)  # Measured duty ratio 33%

    def tx(self, timings, _):  # Ignore toggle
        self.append(timings)
        self.trigger() 


