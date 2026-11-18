"""Explicitly activate a prepared, synthetic recovery generation.

Run with: py -m mpremote connect COM5 run firmware/journal_activate.py
Does not modify the source journal or append observations.
"""
import os
import json
import binascii

MANIFEST = 'recovery-0002.json'
POINTER = 'active-generation.json'
TEMP_POINTER = 'active-generation.json.tmp'
EXPECTED_SOURCE = 'observations-recovery-test.jsonl'
EXPECTED_TARGET = 'observations-0002.jsonl'


def fail(message):
    """Stop activation with an explicit explanation of the failed invariant."""
    raise RuntimeError('ACTIVATION REFUSED: ' + message)


def crc32(data):
    """Calculate a CRC32 checksum for the supplied bytes."""
    return '%08x' % (binascii.crc32(data) & 0xffffffff)


def read_bytes(path):
    """Read a complete file as bytes without modifying it."""
    with open(path, 'rb') as f:
        return f.read()


def exists(path):
    """Check whether a filesystem path already exists."""
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def inspect_source(raw):
    """Validate the preserved predecessor journal and its incomplete final line."""
    lines = raw.split(b'\n')
    # An ending newline creates an empty final split segment.
    complete = lines[:-1]
    tail = lines[-1]
    if not tail:
        fail('source has no unterminated tail')
    if not complete:
        fail('source has no complete records')
    last_seq = None
    for line_number, line in enumerate(complete, 1):
        if not line:
            fail('blank line %d in source' % line_number)
        try:
            env = json.loads(line.decode('utf-8'))
            if env.get('version') != 1:
                fail('unsupported record version on line %d' % line_number)
            payload_json = env['payload_json']
            if crc32(payload_json.encode('utf-8')) != env['crc32']:
                fail('CRC mismatch on line %d' % line_number)
            record = json.loads(payload_json)
            seq = record['seq']
            if type(seq) is not int or seq < 1:
                fail('invalid sequence on line %d' % line_number)
            if last_seq is not None and seq != last_seq + 1:
                fail('nonconsecutive sequence on line %d' % line_number)
            last_seq = seq
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            fail('invalid complete line %d: %s' % (line_number, exc))
    # Only accept a final unterminated line that cannot parse as a complete record.
    try:
        json.loads(tail.decode('utf-8'))
    except (ValueError, UnicodeError):
        pass
    else:
        fail('unterminated tail is valid JSON; manual review required')
    return len(complete), last_seq, len(tail)


if exists(POINTER) or exists(TEMP_POINTER):
    fail('active pointer or temporary pointer already exists; inspect manually')

manifest_raw = read_bytes(MANIFEST)
manifest = json.loads(manifest_raw)
if manifest.get('format_version') != 1:
    fail('unsupported manifest version')
if manifest.get('status') != 'recovery_prepared_not_committed':
    fail('manifest not in prepared state')
if manifest.get('reason') != 'unterminated_invalid_final_line':
    fail('unexpected recovery reason')
if manifest.get('source_preserved') is not True:
    fail('source preservation not asserted')
if manifest.get('source_journal') != EXPECTED_SOURCE:
    fail('unexpected source journal')
if manifest.get('new_journal') != EXPECTED_TARGET:
    fail('unexpected target journal')

source_raw = read_bytes(EXPECTED_SOURCE)
count, last_seq, tail_bytes = inspect_source(source_raw)
if count != manifest.get('validated_prefix_records'):
    fail('validated prefix count changed')
if last_seq != manifest.get('last_valid_sequence'):
    fail('last valid sequence changed')
if tail_bytes != manifest.get('invalid_tail_bytes'):
    fail('invalid tail length changed')
if manifest.get('next_sequence') != last_seq + 1:
    fail('manifest next sequence inconsistent')
if read_bytes(EXPECTED_TARGET) != b'':
    fail('target generation is not empty')

pointer = {
    'format_version': 1,
    'active_journal': EXPECTED_TARGET,
    'source_journal': EXPECTED_SOURCE,
    'recovery_manifest': MANIFEST,
    'next_sequence': last_seq + 1,
    'source_crc32_at_activation': crc32(source_raw),
    'manifest_crc32_at_activation': crc32(manifest_raw),
    'status': 'activated_for_test',
}
# Create temporary file, flush, and rename. Rename atomicity and durability
# depend on filesystem and are not established by this test.
with open(TEMP_POINTER, 'w') as f:
    f.write(json.dumps(pointer) + '\n')
    f.flush()
if json.loads(read_bytes(TEMP_POINTER)) != pointer:
    fail('temporary pointer readback mismatch')
os.rename(TEMP_POINTER, POINTER)
if json.loads(read_bytes(POINTER)) != pointer:
    fail('pointer readback mismatch')

print('Valid prefix records:', count)
print('Last valid sequence:', last_seq)
print('Damaged final line:', count + 1)
print('Invalid tail bytes:', tail_bytes)
print('Source CRC32 at activation:', pointer['source_crc32_at_activation'])
print('Manifest CRC32 at activation:', pointer['manifest_crc32_at_activation'])
print('Active journal:', EXPECTED_TARGET)
print('Next sequence:', last_seq + 1)
print('Pointer:', POINTER)
print('Status: ACTIVATED FOR TEST; no observation appended')
print('NOTE: Source CRC32 was first captured at activation, not preparation')
