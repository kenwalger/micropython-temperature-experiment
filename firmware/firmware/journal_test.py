"""Append an observation to the original v1 internal-flash journal.

Historical learning exercise; does not honor the active-generation pointer."""

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
import os
import binascii

JOURNAL = "observations.jsonl"
# DS3231 RTC address on the I2C bus (GPIO21 SDA, GPIO22 SCL).
RTC_ADDR = 0x68

i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
sensor = ds18x20.DS18X20(onewire.OneWire(Pin(4)))


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


def encode_record(record):
    """Serialize a record once and checksum its exact JSON text bytes."""
    payload_json = json.dumps(record)
    checksum = binascii.crc32(payload_json.encode()) & 0xFFFFFFFF

    envelope = {
        "version": 1,
        "payload_json": payload_json,
        "crc32": "%08x" % checksum,
    }

    return json.dumps(envelope) + "\n"


def validate_line(line):
    """Validate a journal envelope and return its decoded payload."""
    envelope = json.loads(line)

    if envelope.get("version") != 1:
        raise ValueError("Unsupported journal format")

    payload_json = envelope["payload_json"]

    expected = "%08x" % (
        binascii.crc32(payload_json.encode()) & 0xFFFFFFFF
    )

    if expected != envelope["crc32"]:
        raise ValueError("Journal checksum mismatch")

    return json.loads(payload_json)


def read_journal():
    """Read and validate persisted records from the internal filesystem."""
    records = []

    try:
        with open(JOURNAL, "r") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    record = validate_line(line)
                except (ValueError, KeyError, TypeError) as exc:
                    raise ValueError(
                        "Invalid journal record at line %d: %s"
                        % (line_number, exc)
                    )

                records.append(record)

    except OSError as exc:
        if exc.args[0] != 2:
            raise

    return records



def append_record(record):
    """Append a JSONL record and verify it by reading the journal back."""
    line = encode_record(record)

    with open(JOURNAL, "a") as f:
        f.write(line)
        f.flush()

    # Re-read the journal to verify its current contents.
    records = read_journal()
    if not records or records[-1] != record:
        raise RuntimeError("Journal readback verification failed")

    return len(records)


if RTC_ADDR not in i2c.scan():
    raise RuntimeError("DS3231 not detected")

roms = sensor.scan()
if len(roms) != 1:
    raise RuntimeError("Expected exactly one DS18B20")

existing = read_journal()
next_seq = existing[-1]["seq"] + 1 if existing else 1

status_before = i2c.readfrom_mem(RTC_ADDR, 0x0F, 1)[0]

sensor.convert_temp()
time.sleep_ms(750)
temperature = sensor.read_temp(roms[0])

timestamp = rtc_timestamp()
status_after = i2c.readfrom_mem(RTC_ADDR, 0x0F, 1)[0]

if temperature is None or temperature in (85.0, -127.0):
    raise RuntimeError("Invalid temperature")

record = {
    "seq": next_seq,
    "sensor_rom": roms[0].hex(),
    "temperature_c": temperature,
    "read_at_utc": timestamp,
    "rtc_osf": bool((status_before | status_after) & 0x80),
}

count = append_record(record)

print("Appended sequence:", next_seq)
print("Journal records:", count)
print("Observation:", json.dumps(record))
print("Free filesystem bytes:", os.statvfs("/")[0] * os.statvfs("/")[3])
