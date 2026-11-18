"""Discover DS18B20 ROM identifiers without measuring temperature."""
from machine import Pin
import onewire
import ds18x20

sensor = ds18x20.DS18X20(onewire.OneWire(Pin(4)))
roms = sensor.scan()
print('Sensors found:', len(roms))
print('ROM addresses:', [rom.hex() for rom in roms])
