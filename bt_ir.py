"""BLE remote control for transmitting stored infrared commands on a Pico W.

Requires MicroPython with bluetooth support, ir_tx.Player, and keys.Keys.
The Keys class must implement get(name) and list().
"""

import bluetooth
import struct
import time
from machine import Pin
from micropython import const

from ir_tx import Player
from keys import Keys

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

SERVICE_UUID = bluetooth.UUID("4f7b2c81-9d5a-4e2b-b8f3-6c7d1e0a2930")
CHAR_UUID = bluetooth.UUID("4f7b2c81-9d5a-4e2b-b8f3-6c7d1e0a2931")
SERVICE = (SERVICE_UUID, ((CHAR_UUID, bluetooth.FLAG_WRITE),))

IR_PIN = const(17)
MAX_COMMAND_BYTES = const(100)
MAX_PENDING_COMMANDS = const(8)
INTER_KEY_DELAY_MS = const(100)


class BLEStringServer:
    """Accept BLE write commands and transmit matching IR signals."""

    def __init__(self, name="PicoW-String", keys_file="keys.ir"):
        self.name = name
        self.ir_pin = Pin(IR_PIN, Pin.OUT, value=0)
        self.keys = Keys(keys_file)
        print("Available IR keys:", self.keys.list())

        # BLE IRQ only queues commands; IR playback runs in the main loop.
        self.pending_commands = []
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        ((self.char_handle,),) = self.ble.gatts_register_services((SERVICE,))
        self.ble.gatts_set_buffer(self.char_handle, MAX_COMMAND_BYTES)
        self.ble.irq(self.ble_irq)
        self.advertise()

    def advertise(self):
        """Advertise the writable BLE service under a short device name."""
        name = self.name.encode("utf-8")
        # Legacy BLE advertising data is limited to 31 bytes.
        if len(name) > 26:
            raise ValueError("BLE device name is too long (maximum 26 UTF-8 bytes)")

        payload = b"\x02\x01\x06" + struct.pack("BB", len(name) + 1, 0x09) + name
        self.ble.gap_advertise(100_000, adv_data=payload)
        print("Advertising as:", self.name)

    def ble_irq(self, event, data):
        """Handle BLE events without blocking on IR playback or delays."""
        if event == _IRQ_CENTRAL_CONNECT:
            print("Bluetooth client connected")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            print("Bluetooth client disconnected")
            self.advertise()
        elif event == _IRQ_GATTS_WRITE:
            _conn_handle, value_handle = data
            if value_handle != self.char_handle:
                return

            raw = self.ble.gatts_read(self.char_handle)
            if len(self.pending_commands) >= MAX_PENDING_COMMANDS:
                print("Command queue full; ignoring BLE write")
                return
            try:
                command = raw.decode("utf-8")
            except UnicodeError:
                print("Ignoring BLE write: invalid UTF-8")
                return
            self.pending_commands.append(command)

    def transmit_key(self, keyname):
        """Transmit a stored IR key. Return True on success, False otherwise."""
        timings = self.keys.get(keyname)
        if timings is None:
            print("IR key not found:", keyname)
            return False
        if not timings:
            print("IR key has no timing data:", keyname)
            return False

        try:
            # Construct a fresh Player, as in the original implementation.
            player = Player(self.ir_pin, verbose=True)
            print(f"{keyname} {timings}")
            player.play(timings)
        except (OSError, ValueError) as exc:
            print("IR transmission failed for {}: {}".format(keyname, exc))
            return False
        return True

    def handle_command(self, command):
        """Validate and execute a BLE command.

        T <key>      Send a T-series key, e.g. 'T 1' or 'T Menu'.
        D <key>      Send a D-series key, e.g. 'D Stop'.
        Y <key>      Send a Y-series key, e.g. 'Y Tuner'.
        M <digits>   Send 1 to 3 T-series digit keys, e.g. 'M 602'.

        Return True if all requested keys transmit; otherwise False.
        """
        if not isinstance(command, str):
            print("Invalid command: expected a string")
            return False

        parts = command.strip().split()
        if len(parts) != 2:
            print("Invalid command: expected '<operation> <parameter>'")
            return False

        operation = parts[0].upper()
        parameter = parts[1].strip()
        if operation not in ("T", "D", "Y", "M") or not parameter:
            print("Invalid operation or missing parameter:", command)
            return False

        if operation == "M":
            if not (1 <= len(parameter) <= 3) or not all("0" <= c <= "9" for c in parameter):
                print("Invalid M command: provide 1 to 3 digits")
                return False
            for index, digit in enumerate(parameter):
                if not self.transmit_key("T " + digit):
                    return False  # Stop the sequence after a failed key.
                if index < len(parameter) - 1:
                    time.sleep_ms(INTER_KEY_DELAY_MS)
            return True


        # Preserve the spelling/case of the stored key name.
        return self.transmit_key(operation + " " + parameter)

    def run(self):
        """Process queued BLE commands until interrupted."""
        print("BLE string server running")
        try:
            while True:
                if self.pending_commands:
                    command = self.pending_commands.pop(0)
                    print("Received:", command)
                    self.handle_command(command)
                else:
                    time.sleep_ms(20)
        except KeyboardInterrupt:
            print("Stopping BLE server")
        finally:
            self.stop()

    def stop(self):
        """Stop advertising and disable Bluetooth."""
        self.ble.irq(None)
        self.ble.gap_advertise(None)
        self.ble.active(False)
        self.ir_pin.value(0)


if __name__ == "__main__":
    server = BLEStringServer()
    server.run()
