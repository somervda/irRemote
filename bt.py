
import bluetooth
import struct
from micropython import const

from ir_tx import Player
from sys import platform
import time
from machine import Pin
from keys import Keys

# Bluetooth event codes
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# Custom BLE service and characteristic UUIDs
SERVICE_UUID = bluetooth.UUID(
    "12345678-1234-5678-1234-56789abcdef0"
)

CHAR_UUID = bluetooth.UUID(
    "12345678-1234-5678-1234-56789abcdef1"
)

# Characteristic accepts writes from clients
CHARACTERISTIC = (
    CHAR_UUID,
    bluetooth.FLAG_WRITE,
)

SERVICE = (
    SERVICE_UUID,
    (CHARACTERISTIC,),
)

pin17 = Pin(17, Pin.OUT, value = 0)


class BLEStringServer:

    def __init__(self, name="PicoW-String"):
        self.name = name
        self.ble = bluetooth.BLE()
        self.ble.active(True)

        self.ble.irq(self.ble_irq)

        # Register the BLE service
        ((self.char_handle,),) = (
            self.ble.gatts_register_services((SERVICE,))
        )

        # Allow strings up to 100 bytes
        self.ble.gatts_set_buffer(
            self.char_handle, 100
        )

        self.advertise()

        self.keys=Keys("keys.ir")
        print(self.keys.list())

    def advertise(self):
        # BLE advertising payload: flags and device name
        name = self.name.encode("utf-8")

        payload = (
            b"\x02\x01\x06"
            + struct.pack("BB", len(name) + 1, 0x09)
            + name
        )

        # Advertise every 100 milliseconds
        self.ble.gap_advertise(
            100_000, adv_data=payload
        )

        print("Advertising as:", self.name)

    def ble_irq(self, event, data):

        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            print("Bluetooth client connected")

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            print("Bluetooth client disconnected")
            self.advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data

            if value_handle == self.char_handle:
                raw = self.ble.gatts_read(
                    self.char_handle
                )

                message = raw.decode(
                    "utf-8", "replace"
                )

                print("Received:", message)
                self.handle_command(str(message))
                
    def handle_command(self,command):
        """Handle remote commands in the format '<operation> <parameter>'.

        Operations
        ----------
        T <key>   Transmit a single T-series key  (e.g. 'T 1', 'T Menu')
        D <key>   Transmit a single D-series key  (e.g. 'D Stop', 'D Popup')
        Y <Key>   Transmit a single Y-series key  (e.g. 'Y Tuner' to swap yamaha reciever to the tuner input)
        M <digits> Transmit up to 3 T-series keys in sequence
                    (e.g. 'M 123' → T 1, T 2, T 3)
                    (e.g. 'M 602' → T 6, T 0, T 2)
        """
        parts = command.split()

        if len(parts) < 2:
            print(f"Invalid command: {command!r}  (expected '<operation> <parameter>')")
            return

        operation, parameter = parts[0].upper(), parts[1]
        print(f"Operation:{operation} Parameter:{parameter}")



        if operation == "M":
            print(f"M {parameter}")
            # Each character (up to 3) becomes a T-series key, sent in order``
            for digit in parameter[:3]:
                print(digit)
                keyname=(f"T {str(digit)}")
                print(keyname)
                times=self.keys.get(keyname)
                print(times)
                if times:
                    ir = Player(pin17,verbose=True)
                    print(f"Playing {keyname}")
                    ir.play(times)
                else:
                    print(f"key not found: {keyname}")
                # Short delay between it transmitions of multiple keys
                time.sleep(0.1)
        else:
            times=self.keys.get(command)
            if times:
                ir = Player(pin17,verbose=True)
                ir.play(times)
            else:
                print(f"command not found: {command}")    
            
            
# Start the BLE server
server = BLEStringServer()

print("BLE string server running")
