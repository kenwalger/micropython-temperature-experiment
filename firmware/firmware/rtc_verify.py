"""Read the DS3231 RTC and oscillator-stop flag without modifying either."""

# Hardware wiring for this experiment (ESP32-WROVER):
#   Waterproof DS18B20: yellow/data -> GPIO4, red/VCC -> 3V3, black/GND -> GND.
#   The terminal adapter provides the required OneWire pull-up resistor.
#   DS3231 RTC: SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND.
#   DS3231 I2C address 0x68; address 0x57 may be onboard EEPROM.
# GPIO numbers are ESP32 GPIO identifiers, NOT physical header pin positions.


from machine import Pin, I2C
import time

# DS3231 RTC address on the I2C bus (GPIO21 SDA, GPIO22 SCL).
RTC_ADDR = 0x68
# DS3231 status register: bit 7 is the oscillator-stop flag (OSF).
STATUS_REG = 0x0F

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)


def unbcd(value):
    """Decode a binary-coded decimal (BCD) register value into an integer."""
    return ((value >> 4) * 10) + (value & 0x0F)


def read_rtc():
    """Read and decode the DS3231 date and time registers."""
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
