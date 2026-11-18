"""Combine a DS18B20 reading and DS3231 RTC timestamp into one observation.

Read-only with respect to journal files."""

# Hardware wiring for this experiment (ESP32-WROVER):
#   Waterproof DS18B20: yellow/data -> GPIO4, red/VCC -> 3V3, black/GND -> GND.
#   The terminal adapter provides the required OneWire pull-up resistor.
#   DS3231 RTC: SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND.
#   DS3231 I2C address 0x68; address 0x57 may be onboard EEPROM.
# GPIO numbers are ESP32 GPIO identifiers, NOT physical header pin positions.


from machine import Pin, I2C
import onewire
import ds18x20
import time
import json

# DS18B20 OneWire data line (yellow wire) on ESP32 GPIO4.
SENSOR_PIN = 4
# DS3231 RTC address on the I2C bus (GPIO21 SDA, GPIO22 SCL).
RTC_ADDR = 0x68
# DS3231 status register: bit 7 is the oscillator-stop flag (OSF).
STATUS_REG = 0x0F

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
sensor = ds18x20.DS18X20(onewire.OneWire(Pin(SENSOR_PIN)))


def unbcd(value):
    """Decode a binary-coded decimal (BCD) register value into an integer."""
    return ((value >> 4) * 10) + (value & 0x0F)


def rtc_timestamp():
    """Format the DS3231 RTC register values as a UTC-style timestamp string."""
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
