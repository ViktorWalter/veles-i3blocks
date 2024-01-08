#!/usr/bin/env python3.9
import minimalmodbus
from veles.device import SensorWiredIAQ
from veles.device.generic import NoResponseError
import sys
import serial
import time
import random
from filelock import Timeout, FileLock
from math import log10, ceil

# Default values for my sensor (your address will probably differ).
addr = 109
new_addr = 110
baud = 19200
register_name = "LED_ON"

# Parse parameters.
if len(sys.argv) > 1:
    if sys.argv[1] == "--help":
        print("usage: ./read_value.py [register name] [modbus address] [OS device name]")
        exit(0)

if len(sys.argv) > 4:
    register_name = str(sys.argv[4])
else:
    register_name = "LED_ON"

if len(sys.argv) > 3:
    new_addr = int(sys.argv[3])
else:
    new_addr = 110

if len(sys.argv) > 2:
    addr = int(sys.argv[2])
else:
    addr = 109

if len(sys.argv) > 1:
    dev = sys.argv[1]
else:
    dev = "ttyUSB0"

reg_number = SensorWiredIAQ.holding_registers[register_name]
# reg_number = SensorWiredIAQ.holding_registers["LED_ON"]

# Generate a temp file lock to ensure the device is only opened by a single process at once.
lock = FileLock("/tmp/veles_{}.lock".format(dev), timeout=1.5)

# Try to lock the file and perform the readout on the device.
try:
    with lock:
        try:
            s = SensorWiredIAQ(modbus_address=addr, baudrate=baud, dev="/dev/"+dev)
        except (serial.serialutil.SerialException, minimalmodbus.NoResponseError):
            print("device busy")
            exit(1)
        try:
            # Obtain the value of the register.
            reg_val = int(s.read_register(reg_number))
            print("Prev value: "+ str(reg_val))
            reg_val = int(s.write_register(reg_number,new_addr))

            # Find the corresponding unit display test and unit multiple.
            reg_multiple = reg_multiples[reg_name]
            reg_unit = reg_units[reg_name]

            # Recalculate the value of the register to the respective units.
            reg_val_in_unit = reg_val/reg_multiple

            # If the multiple is > 1, there will be some decimals when the register value
            # is recalculated to the proper units. Make sure the decimals are displayed properly
            # while not displaying decimals for multipliers <= 1.
            if reg_multiple > 1:
                order_of_magnitude = int(ceil(log10(reg_multiple)))
                extra_digits_to_display = max((order_of_magnitude, 0))
            else:
                extra_digits_to_display = 0

            # Format the value (now in the correct units) and finally print it.
            digits_txt = "{}".format(extra_digits_to_display)
            fmt = "{:."+digits_txt+"f}{}"
            print(fmt.format(reg_val_in_unit, reg_unit))

        except minimalmodbus.IllegalRequestError:
            print("unknown")
            exit(1)
except Timeout:
    print("device busy")
    exit(1)
