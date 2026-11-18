"""Read-only validation of a v1 JSONL journal; never repairs or appends."""
import json
import binascii
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'observations-recovery-test.jsonl'


def validate(line):
    """Validate one JSONL envelope and return its observation payload."""
    envelope = json.loads(line)
    if envelope.get('version') != 1:
        raise ValueError('unsupported journal version')
    payload = envelope['payload_json']
    if not isinstance(payload, str):
        raise ValueError('payload_json is not a string')
    expected = '%08x' % (binascii.crc32(payload.encode()) & 0xffffffff)
    if envelope['crc32'] != expected:
        raise ValueError('CRC32 mismatch')
    record = json.loads(payload)
    if not isinstance(record, dict) or not isinstance(record.get('seq'), int):
        raise ValueError('missing integer sequence')
    return record


def inspect(path):
    """Report valid prefix length and the first invalid journal line."""
    count = 0
    last_seq = None
    try:
        with open(path, 'r') as f:
            for number, line in enumerate(f, 1):
                try:
                    if not line.endswith('\n'):
                        raise ValueError('line missing terminating newline')
                    record = validate(line)
                    if last_seq is not None and record['seq'] != last_seq + 1:
                        raise ValueError('sequence discontinuity')
                except (ValueError, KeyError, TypeError) as exc:
                    print('INVALID line %d: %s' % (number, exc))
                    print('VALID prefix records:', count)
                    print('Last valid sequence:', last_seq)
                    print('Append allowed: NO')
                    return False
                count += 1
                last_seq = record['seq']
    except OSError as exc:
        print('Cannot open journal:', exc)
        return False
    print('VALID prefix records:', count)
    print('Last valid sequence:', last_seq)
    print('Append allowed: YES (validation only; no append performed)')
    return True


inspect(PATH)
