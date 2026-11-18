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
