# Hardware wiring for this experiment (ESP32-WROVER):
#   Waterproof DS18B20: yellow/data -> GPIO4, red/VCC -> 3V3, black/GND -> GND.
#   The terminal adapter provides the required OneWire pull-up resistor.
#   DS3231 RTC: SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND.
#   DS3231 I2C address 0x68; address 0x57 may be onboard EEPROM.
# GPIO numbers are ESP32 GPIO identifiers, NOT physical header pin positions.

"""Discover DS18B20 ROM identifiers without measuring temperature."""
from machine import Pin
import onewire
import ds18x20

sensor = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
roms = sensor.scan()
print('Sensors found:', len(roms))
print('ROM addresses:', [rom.hex() for rom in roms])
