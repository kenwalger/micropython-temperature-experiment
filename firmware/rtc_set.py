
from machine import Pin, I2C
import sys
import time

RTC_ADDR = 0x68
STATUS_REG = 0x0F

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)


def bcd(value):
    return ((value // 10) << 4) | (value % 10)


def unbcd(value):
    return ((value >> 4) * 10) + (value & 0x0F)


def read_rtc():
    raw = i2c.readfrom_mem(RTC_ADDR, 0x00, 7)
    second = unbcd(raw[0] & 0x7F)
    minute = unbcd(raw[1] & 0x7F)
    hour = unbcd(raw[2] & 0x3F)
    day = unbcd(raw[4] & 0x3F)
    month = unbcd(raw[5] & 0x1F)
    year = 2000 + unbcd(raw[6])
    if raw[5] & 0x80:
        year += 100
    return (year, month, day, hour, minute, second)


def set_rtc(year, month, day, hour, minute, second):
    if not (2000 <= year <= 2099):
        raise ValueError("Year must be 2000-2099")

    # DS3231 weekday: 1-7; compute from date.
    weekday = time.localtime(
        time.mktime((year, month, day, 0, 0, 0, 0, 0))
    )[6] + 1

    data = bytes([
        bcd(second),
        bcd(minute),
        bcd(hour),
        bcd(weekday),
        bcd(day),
        bcd(month),
        bcd(year - 2000),
    ])
    i2c.writeto_mem(RTC_ADDR, 0x00, data)


if RTC_ADDR not in i2c.scan():
    raise RuntimeError("DS3231 not detected")

from rtc_config import UTC_TIMESTAMP
stamp = UTC_TIMESTAMP

date_part, time_part = stamp.split("T")
year, month, day = [int(x) for x in date_part.split("-")]
hour, minute, second = [int(x) for x in time_part.split(":")]

status_before = i2c.readfrom_mem(RTC_ADDR, STATUS_REG, 1)[0]
print("OSF before:", bool(status_before & 0x80))

set_rtc(year, month, day, hour, minute, second)

first = read_rtc()
print("RTC after setting:", first)

time.sleep(2)
second_read = read_rtc()
print("RTC after 2 seconds:", second_read)

# Verify date/time matches and clock is advancing.
if first[:5] != (year, month, day, hour, minute):
    raise RuntimeError("RTC date/time verification failed")

if time.mktime(second_read + (0, 0)) <= time.mktime(first + (0, 0)):
    raise RuntimeError("RTC does not appear to be advancing")

# Clear OSF while preserving other status bits.
status = i2c.readfrom_mem(RTC_ADDR, STATUS_REG, 1)[0]
i2c.writeto_mem(RTC_ADDR, STATUS_REG, bytes([status & 0x7F]))

status_after = i2c.readfrom_mem(RTC_ADDR, STATUS_REG, 1)[0]
print("OSF after:", bool(status_after & 0x80))
print("RTC initialization complete")
