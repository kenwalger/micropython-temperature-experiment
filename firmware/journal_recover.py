"""Explicit, non-destructive recovery from a truncated FINAL journal line.

Test-only defaults. Does not modify the damaged source or production journal.
Not a crash-atomic transaction or a production recovery supervisor.
"""
import binascii
import json
import os

SOURCE = 'observations-recovery-test.jsonl'
NEW_JOURNAL = 'observations-0002.jsonl'
MANIFEST = 'recovery-0002.json'


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError as exc:
        if exc.args[0] == 2:
            return False
        raise


def validated_record(line):
    if not line.endswith(b'\n'):
        raise ValueError('missing terminating newline')
    envelope = json.loads(line)
    if envelope.get('version') != 1:
        raise ValueError('unsupported envelope version')
    payload = envelope['payload_json']
    if not isinstance(payload, str):
        raise ValueError('payload_json must be a string')
    crc = '%08x' % (binascii.crc32(payload.encode()) & 0xffffffff)
    if envelope['crc32'] != crc:
        raise ValueError('CRC32 mismatch')
    record = json.loads(payload)
    if not isinstance(record, dict) or type(record.get('seq')) is not int:
        raise ValueError('missing integer sequence')
    return record


def inspect_source():
    with open(SOURCE, 'rb') as f:
        lines = f.readlines()
    if len(lines) < 2:
        raise RuntimeError('Expected valid records followed by a truncated tail')

    last_seq = None
    for index, line in enumerate(lines[:-1], 1):
        try:
            record = validated_record(line)
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError('Corruption before tail at line %d: %s' % (index, exc))
        seq = record['seq']
        if last_seq is None:
            if seq != 1:
                raise RuntimeError('Expected initial sequence 1')
        elif seq != last_seq + 1:
            raise RuntimeError('Sequence gap at line %d' % index)
        last_seq = seq

    # This recovery policy only accepts a physically unterminated final line.
    # A newline-terminated but invalid record requires manual investigation.
    tail = lines[-1]
    if tail.endswith(b'\n'):
        raise RuntimeError('Final line is terminated; refusing automatic recovery')
    try:
        validated_record(tail)
    except (ValueError, KeyError, TypeError):
        pass
    else:
        raise RuntimeError('Unexpected valid final line')
    return len(lines) - 1, last_seq, len(tail)


if exists(NEW_JOURNAL) or exists(MANIFEST):
    raise RuntimeError('Recovery outputs already exist; refusing to overwrite')

count, last_seq, tail_bytes = inspect_source()
next_seq = last_seq + 1
manifest = {
    'format_version': 1,
    'source_journal': SOURCE,
    'new_journal': NEW_JOURNAL,
    'reason': 'unterminated_invalid_final_line',
    'validated_prefix_records': count,
    'last_valid_sequence': last_seq,
    'next_sequence': next_seq,
    'invalid_tail_bytes': tail_bytes,
    'source_preserved': True,
    'status': 'recovery_prepared_not_committed',
}

# Write manifest before creating the new journal. A crash between operations
# leaves an inspectable partial transition; rerun will refuse to overwrite.
with open(MANIFEST, 'w') as f:
    f.write(json.dumps(manifest) + '\n')
    f.flush()

with open(NEW_JOURNAL, 'wb') as f:
    f.flush()

print('Valid prefix records:', count)
print('Last valid sequence:', last_seq)
print('Damaged final line:', count + 1)
print('Invalid tail bytes:', tail_bytes)
print('Original preserved:', SOURCE)
print('New empty generation:', NEW_JOURNAL)
print('Next sequence reserved:', next_seq)
print('Manifest:', MANIFEST)
print('Status: PREPARED; no production writer has been switched')
