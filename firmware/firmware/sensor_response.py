# Hardware wiring for this experiment (ESP32-WROVER):
#   Waterproof DS18B20: yellow/data -> GPIO4, red/VCC -> 3V3, black/GND -> GND.
#   The terminal adapter provides the required OneWire pull-up resistor.
#   DS3231 RTC: SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND.
#   DS3231 I2C address 0x68; address 0x57 may be onboard EEPROM.
# GPIO numbers are ESP32 GPIO identifiers, NOT physical header pin positions.

"""Collect five temperature samples with an explicit conversion each time."""
from machine import Pin
import onewire
import ds18x20
import time

sensor = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
roms = sensor.scan()
if len(roms) != 1:
    raise RuntimeError('Expected one DS18B20; found %d' % len(roms))

for sample in range(1, 6):
    sensor.convert_temp()
    time.sleep_ms(750)
    value = sensor.read_temp(roms[0])
    if value is None or value in (85.0, -127.0):
        raise RuntimeError('Invalid temperature reading')
    print('Sample %d: %.4f C' % (sample, value))
    if sample != 5:
        time.sleep(2)
