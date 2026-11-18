
from machine import Pin, I2C
import time

RTC_ADDR = 0x68
STATUS_REG = 0x0F

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)


def unbcd(value):
    return ((value >> 4) * 10) + (value & 0x0F)


def read_rtc():
    raw = i2c.readfrom_mem(RTC_ADDR, 0x00, 7)

    year = 2000 + unbcd(raw[6])
    if raw[5] & 0x80:
        year += 100

    return (
        year,
        unbcd(raw[5] & 0x1F),
        unbcd(raw[4] & 0x3F),
        unbcd(raw[2] & 0x3F),
        unbcd(raw[1] & 0x7F),
        unbcd(raw[0] & 0x7F),
    )


if RTC_ADDR not in i2c.scan():
    raise RuntimeError("DS3231 not detected")

status = i2c.readfrom_mem(RTC_ADDR, STATUS_REG, 1)[0]
timestamp = read_rtc()

print("RTC UTC: %04d-%02d-%02dT%02d:%02d:%02dZ" % timestamp)
print("Oscillator-stop flag:", bool(status & 0x80))
print("Clock status:", "UNTRUSTED" if status & 0x80 else "NO STOP FLAG")
