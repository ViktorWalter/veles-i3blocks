# VelesLabs i3blocks utils

This repository contains a utility script for integrating the VelesLabs wired IAQ sensor with i3wm's i3blocks information bar (see image below).
The script ensures mutually exclusive access to the device to prevent reading errors (the communication will typically fail if you try to read a register by two processes in parallel).

Tested with:
 * Ubuntu 20.04
 * Python 3.9
 * Veles Python library version 0.1.0

![i3blocks_screenshot](i3blocks_screenshot.png)

## Usage

For usage, call `./read_value.py --help`:
  * `[register name]` -- name of the register in the sensor to read. A list of the available registers can be obtained from the Veles Python API.
  * `[modbus address]` -- address of the sensor modbus device. You should receive this with the physical sensor or you can use the enumeration tool from the Veles Python library.
  * `[OS device name]` -- name of the TTY device corresponding to the sensor in your OS (without the `/dev/` path prefix). If you're not using custom udev rules, this will typically be `ttyUSB0` or similar.

The script will create a lock file for the device's OS file handle, read out the desired register's value from the device, and print it to `stdout` including its physical unit.
