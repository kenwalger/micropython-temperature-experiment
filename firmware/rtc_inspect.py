from machine import Pin, I2C
import time

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)

devices = i2c.scan()
print("I2C devices:", [hex(a) for a in devices])

if 0x68 not in devices:
    raise RuntimeError("DS3231 not detected")

status = i2c.readfrom_mem(0x68, 0x0F, 1)[0]
raw = i2c.readfrom_mem(0x68, 0x00, 7)

print("RTC status:", hex(status))
print("Oscillator stopped:", bool(status & 0x80))
print("Raw time registers:", raw.hex())