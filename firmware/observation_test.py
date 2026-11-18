
from machine import Pin, I2C
import onewire
import ds18x20
import time
import json

SENSOR_PIN = 4
RTC_ADDR = 0x68
STATUS_REG = 0x0F

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
sensor = ds18x20.DS18X20(onewire.OneWire(Pin(SENSOR_PIN)))


def unbcd(value):
    return ((value >> 4) * 10) + (value & 0x0F)


def rtc_timestamp():
    raw = i2c.readfrom_mem(RTC_ADDR, 0x00, 7)

    year = 2000 + unbcd(raw[6])
    if raw[5] & 0x80:
        year += 100

    values = (
        year,
        unbcd(raw[5] & 0x1F),
        unbcd(raw[4] & 0x3F),
        unbcd(raw[2] & 0x3F),
        unbcd(raw[1] & 0x7F),
        unbcd(raw[0] & 0x7F),
    )

    return "%04d-%02d-%02dT%02d:%02d:%02dZ" % values


devices = i2c.scan()
if RTC_ADDR not in devices:
    raise RuntimeError("DS3231 not detected")

roms = sensor.scan()
if len(roms) != 1:
    raise RuntimeError("Expected one DS18B20, found %d" % len(roms))

# Check clock status before the observation.
status_before = i2c.readfrom_mem(RTC_ADDR, STATUS_REG, 1)[0]

sensor.convert_temp()
time.sleep_ms(750)
temperature = sensor.read_temp(roms[0])

# Timestamp after conversion; this is the readout time.
observed_at = rtc_timestamp()

# Check status again so we don't silently ignore a stop flag.
status_after = i2c.readfrom_mem(RTC_ADDR, STATUS_REG, 1)[0]
rtc_osf = bool((status_before | status_after) & 0x80)

if temperature is None or temperature in (85.0, -127.0):
    raise RuntimeError("Invalid temperature reading")

record = {
    "sensor_rom": roms[0].hex(),
    "temperature_c": temperature,
    "read_at_utc": observed_at,
    "timestamp_basis": "rtc_after_conversion",
    "rtc_osf": rtc_osf,
    "clock_status": "untrusted" if rtc_osf else "no_stop_flag",
}

print(json.dumps(record))
