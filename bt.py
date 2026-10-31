
import bluetooth
import struct
from micropython import const

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


# Start the BLE server
server = BLEStringServer()

print("BLE string server running")
