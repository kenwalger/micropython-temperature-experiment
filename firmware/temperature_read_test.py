"""Test a DS18B20 temperature reading on an ESP32 running MicroPython.

Hardware used in the article:
    DS18B20 yellow/data  -> ESP32 GPIO4
    DS18B20 red/power    -> ESP32 3V3
    DS18B20 black/ground -> ESP32 GND
    The terminal adapter provides the OneWire pull-up resistor.

Run from the project root (Windows PowerShell):
    py -m mpremote connect COM5 run firmware/temperature_read_test.py
"""

import time
from machine import Pin
import onewire
import ds18x20

SENSOR_PIN = 4  # ESP32 GPIO4, not physical header pin 4.


def read_temperature_c(sensor, rom: bytes, wait_ms: int = 750) -> float:
    """Request a DS18B20 conversion and read the temperature.

    Args:
        sensor: Configured DS18X20 sensor interface.
        rom: Sensor identifier returned by scan().
        wait_ms: Conversion wait in milliseconds (750 for 12-bit resolution).

    Returns:
        Temperature in degrees Celsius.

    Raises:
        RuntimeError: If the sensor returns an invalid reading.
    """
    sensor.convert_temp()
    time.sleep_ms(wait_ms)
    temperature = sensor.read_temp(rom)

    # 85 C is a possible power-on default, but can be a real measurement.
    # Rejecting it is a conservative choice for this wine-storage test.
    if temperature is None or temperature in (85.0, -127.0):
        raise RuntimeError("Invalid temperature reading: {}".format(temperature))

    return temperature


def main():
    bus = onewire.OneWire(Pin(SENSOR_PIN))
    sensor = ds18x20.DS18X20(bus)
    roms = sensor.scan()
    print("Sensors found:", len(roms))

    if not roms:
        raise RuntimeError("No DS18B20 found on GPIO{}".format(SENSOR_PIN))

    for rom in roms:
        rom_hex = "".join("{:02x}".format(value) for value in rom)
        temperature = read_temperature_c(sensor, rom)
        print("ROM:", rom_hex)
        print("Temperature (C):", temperature)


main()
