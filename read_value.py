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
baud = 19200

# Parse parameters.
if len(sys.argv) > 1:
    if sys.argv[1] == "--help":
        print("usage: ./read_value.py [register name] [modbus address] [OS device name]")
        exit(0)
    reg_name = sys.argv[1]
else:
    reg_name = "CO2"

if len(sys.argv) > 2:
    addr = int(sys.argv[2])
else:
    addr = 109

if len(sys.argv) > 3:
    dev = sys.argv[3]
else:
    dev = "ttyUSB0"

# Check validity of parameters.
read_reg_names = SensorWiredIAQ.input_registers
if reg_name not in read_reg_names:
    print("unknown".format(reg_name))
    exit(1)
reg_number = SensorWiredIAQ.input_registers[reg_name]

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

        # Measurement units corresponding to the register values.
        reg_units = {
                "T": "°C",  # 
                "T_F": "F",  # deg F
                "RH": "%",  # %, from SHT4x
                "CO2": "ppm",  # ppm
                "VOC_INDEX": "",  # VOC index as calculated by Sensirion library (1 to 500, average 100)
                "VOC_TICKS": "",  # raw VOC ticks
                "PMC_MASS_1_0": "ug/m^3",  # ug / m^3
                "PMC_MASS_2_5": "ug/m^3",  # ug / m^3
                "PMC_MASS_4_0": "ug/m^3",  # ug / m^3
                "PMC_MASS_10_0": "ug/m^3",  # ug / m^3
                "PMC_NUMBER_0_5": "1/m^3",  # 1 / m^3
                "PMC_NUMBER_1_0": "1/m^3",  # 1 / m^3
                "PMC_NUMBER_2_5": "1/m^3",  # 1 / m^3
                "PMC_NUMBER_4_0": "1/m^3",  # 1 / m^3
                "PMC_NUMBER_10_0": "1/m^3",  # 1 / m^3
                "PMC_TYPICAL_PARTICLE_SIZE": "nm",  # nm
                "READ_ERR_T": "",  # temperature sensor error code (0 if no error)
                "READ_ERR_RH": "",  # humidity sensor error code (0 if no error)
                "READ_ERR_CO2": "",  # CO2 sensor error code (0 if no error)
                "READ_ERR_VOC": "",  # VOC sensor error code (0 if no error)
                "READ_ERR_PMC": "",  # PMC sensor error code (0 if no error)
            }

        # The values in the registers are not always stored directly in the units e.g. to improve accuracy.
        # This dict stores the respective multipliers of the registers.
        reg_multiples = {
                "T": 10,  # 
                "T_F": 10,  # deg F
                "RH": 1,  # %, from SHT4x
                "CO2": 1,  # ppm
                "VOC_INDEX": 1,  # VOC index as calculated by Sensirion library (1 to 500, average 100)
                "VOC_TICKS": 1,  # raw VOC ticks
                "PMC_MASS_1_0": 1,  # ug / m^3
                "PMC_MASS_2_5": 1,  # ug / m^3
                "PMC_MASS_4_0": 1,  # ug / m^3
                "PMC_MASS_10_0": 1,  # ug / m^3
                "PMC_NUMBER_0_5": 1,  # 1 / m^3
                "PMC_NUMBER_1_0": 1,  # 1 / m^3
                "PMC_NUMBER_2_5": 1,  # 1 / m^3
                "PMC_NUMBER_4_0": 1,  # 1 / m^3
                "PMC_NUMBER_10_0": 1,  # 1 / m^3
                "PMC_TYPICAL_PARTICLE_SIZE": 1,  # nm
                "READ_ERR_T": 1,  # temperature sensor error code (0 if no error)
                "READ_ERR_RH": 1,  # humidity sensor error code (0 if no error)
                "READ_ERR_CO2": 1,  # CO2 sensor error code (0 if no error)
                "READ_ERR_VOC": 1,  # VOC sensor error code (0 if no error)
                "READ_ERR_PMC": 1,  # PMC sensor error code (0 if no error)
            }

        try:
            # Obtain the value of the register.
            reg_val = int(s.read_register(reg_number))

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
