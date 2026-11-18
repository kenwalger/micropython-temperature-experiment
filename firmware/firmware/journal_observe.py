# Hardware wiring for this experiment (ESP32-WROVER):
#   Waterproof DS18B20: yellow/data -> GPIO4, red/VCC -> 3V3, black/GND -> GND.
#   The terminal adapter provides the required OneWire pull-up resistor.
#   DS3231 RTC: SDA -> GPIO21, SCL -> GPIO22, VCC -> 3V3, GND -> GND.
#   DS3231 I2C address 0x68; address 0x57 may be onboard EEPROM.
# GPIO numbers are ESP32 GPIO identifiers, NOT physical header pin positions.

"""Append one RTC-timestamped DS18B20 observation to the activated journal.

Run on ESP32 with: mpremote connect COM5 run firmware/journal_observe.py
No main.py is installed or modified. The recovery source is read-only.
"""

import binascii
import json
import os
import time
from machine import I2C, Pin
import onewire
import ds18x20

POINTER = 'active-generation.json'
EXPECTED_SOURCE = 'observations-recovery-test.jsonl'
EXPECTED_MANIFEST = 'recovery-0002.json'
EXPECTED_ACTIVE = 'observations-0002.jsonl'
# DS18B20 OneWire data line (yellow wire) on ESP32 GPIO4.
SENSOR_PIN = 4
# DS3231 RTC address on the I2C bus (GPIO21 SDA, GPIO22 SCL).
RTC_ADDRESS = 0x68


def crc32_hex(data):
    """CRC32 of bytes, represented as eight lowercase hexadecimal digits."""
    return '%08x' % (binascii.crc32(data) & 0xffffffff)


def read_bytes(path):
    """Read a complete file as bytes without modifying it."""
    with open(path, 'rb') as f:
        return f.read()


def require(condition, message):
    """Raise an error when a required journal invariant is not satisfied."""
    if not condition:
        raise ValueError(message)


def valid_record(line):
    """Decode one newline-terminated v1 envelope without reserializing payload."""
    require(line.endswith(b'\n'), 'unterminated record')
    envelope = json.loads(line.decode('utf-8'))
    require(envelope.get('version') == 1, 'unsupported record version')
    payload_json = envelope['payload_json']
    require(isinstance(payload_json, str), 'payload_json must be text')
    require(crc32_hex(payload_json.encode('utf-8')) == envelope['crc32'],
            'record CRC32 mismatch')
    record = json.loads(payload_json)
    require(isinstance(record.get('seq'), int), 'missing integer sequence')
    return record


def inspect_source(raw):
    """Require exactly three valid records and an invalid, unterminated tail."""
    lines = raw.splitlines(keepends=True)
    require(len(lines) == 4, 'unexpected predecessor line count')
    previous = 0
    for index, line in enumerate(lines[:3], 1):
        record = valid_record(line)
        require(record['seq'] == previous + 1,
                'predecessor sequence mismatch at line %d' % index)
        previous = record['seq']
    tail = lines[3]
    require(not tail.endswith(b'\n'), 'predecessor tail is terminated')
    require(len(tail) == 39, 'predecessor tail length changed')
    # The experiment injected malformed JSON; reject a valid but unterminated record.
    try:
        json.loads(tail.decode('utf-8'))
    except (ValueError, UnicodeError):
        pass
    else:
        raise ValueError('unterminated tail is valid JSON; refuse recovery')
    return previous


def inspect_active(raw, start_seq):
    """Return next sequence, rejecting incomplete records, gaps and duplicates."""
    next_seq = start_seq
    if not raw:
        return next_seq, 0
    count = 0
    for line in raw.splitlines(keepends=True):
        record = valid_record(line)
        require(record['seq'] == next_seq,
                'active journal sequence gap or duplicate')
        next_seq += 1
        count += 1
    return next_seq, count


def bcd(value):
    """Encode an integer into binary-coded decimal (BCD) for RTC registers."""
    return (value & 0x0f) + 10 * ((value >> 4) & 0x0f)


def rtc_read(i2c):
    """Read DS3231 UTC clock; refuse oscillator-stop or invalid time fields."""
    status = i2c.readfrom_mem(RTC_ADDRESS, 0x0f, 1)[0]
    require((status & 0x80) == 0, 'RTC oscillator-stop flag is set')
    data = i2c.readfrom_mem(RTC_ADDRESS, 0x00, 7)
    sec = bcd(data[0] & 0x7f)
    minute = bcd(data[1] & 0x7f)
    hour_reg = data[2]
    require((hour_reg & 0x40) == 0, 'RTC is in 12-hour mode')
    hour = bcd(hour_reg & 0x3f)
    day = bcd(data[4] & 0x3f)
    month = bcd(data[5] & 0x1f)
    year = 2000 + bcd(data[6]) + (100 if (data[5] & 0x80) else 0)
    require(2020 <= year <= 2099 and 1 <= month <= 12 and
            1 <= day <= 31 and hour <= 23 and minute <= 59 and sec <= 59,
            'RTC date/time fields out of range')
    return '%04d-%02d-%02dT%02d:%02d:%02dZ' % (
        year, month, day, hour, minute, sec)


def observation(seq):
    """Take one conversion, then timestamp its readout using the DS3231."""
    sensor = ds18x20.DS18X20(onewire.OneWire(Pin(SENSOR_PIN)))
    roms = sensor.scan()
    require(len(roms) == 1, 'expected exactly one DS18B20 sensor')
    sensor.convert_temp()
    time.sleep_ms(750)
    temperature = sensor.read_temp(roms[0])
    require(temperature is not None and -55 <= temperature <= 125,
            'invalid DS18B20 temperature')
    i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)
    timestamp = rtc_read(i2c)
    return {
        'seq': seq,
        'read_at_utc': timestamp,
        'timestamp_basis': 'rtc_after_conversion',
        'rtc_osf': False,
        'sensor_rom': binascii.hexlify(roms[0]).decode(),
        'temperature_c': temperature,
    }


def main():
    """Validate recovery state and append one observation to the active generation."""
    pointer_raw = read_bytes(POINTER)
    pointer = json.loads(pointer_raw.decode('utf-8'))
    require(pointer.get('format_version') == 1 and
            pointer.get('status') == 'activated_for_test',
            'pointer not activated for test')
    require(pointer.get('source_journal') == EXPECTED_SOURCE and
            pointer.get('recovery_manifest') == EXPECTED_MANIFEST and
            pointer.get('active_journal') == EXPECTED_ACTIVE,
            'unexpected journal paths in pointer')
    require(pointer.get('next_sequence') == 4, 'unexpected initial sequence')

    source_raw = read_bytes(EXPECTED_SOURCE)
    manifest_raw = read_bytes(EXPECTED_MANIFEST)
    require(crc32_hex(source_raw) == pointer['source_crc32_at_activation'],
            'predecessor changed since activation')
    require(crc32_hex(manifest_raw) == pointer['manifest_crc32_at_activation'],
            'recovery manifest changed since activation')
    manifest = json.loads(manifest_raw.decode('utf-8'))
    require(manifest.get('format_version') == 1 and
            manifest.get('status') == 'recovery_prepared_not_committed' and
            manifest.get('source_journal') == EXPECTED_SOURCE and
            manifest.get('new_journal') == EXPECTED_ACTIVE and
            manifest.get('validated_prefix_records') == 3 and
            manifest.get('last_valid_sequence') == 3 and
            manifest.get('next_sequence') == 4 and
            manifest.get('invalid_tail_bytes') == 39,
            'recovery manifest inconsistent')
    require(inspect_source(source_raw) == 3,
            'predecessor validation failed')

    active_raw = read_bytes(EXPECTED_ACTIVE)
    seq, prior_count = inspect_active(active_raw, 4)
    record = observation(seq)
    payload_json = json.dumps(record)
    line = (json.dumps({
        'version': 1,
        'payload_json': payload_json,
        'crc32': crc32_hex(payload_json.encode('utf-8')),
    }) + '\n').encode('utf-8')

    with open(EXPECTED_ACTIVE, 'ab') as f:
        f.write(line)
        f.flush()
    # This is a readback check, NOT a guarantee against sudden power loss.
    written_raw = read_bytes(EXPECTED_ACTIVE)
    require(written_raw == active_raw + line,
            'post-append journal bytes differ from expected')
    next_seq, count = inspect_active(written_raw, 4)
    require(count == prior_count + 1 and next_seq == seq + 1,
            'post-append validation failed')
    print('Appended sequence:', seq)
    print('Active journal:', EXPECTED_ACTIVE)
    print('Journal records:', count)
    print('Observation:', json.dumps(record))
    print('Source and recovery evidence: unchanged by this script')


main()
