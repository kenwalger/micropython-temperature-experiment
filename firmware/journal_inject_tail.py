"""Deliberately damage ONLY the dedicated test journal. Never use on production."""
SOURCE = 'observations.jsonl'
TARGET = 'observations-recovery-test.jsonl'

# Refuse to overwrite an existing test artifact.
try:
    with open(TARGET, 'rb'):
        raise RuntimeError('Test journal already exists; refusing to overwrite')
except OSError as exc:
    if exc.args[0] != 2:
        raise

with open(SOURCE, 'rb') as src:
    baseline = src.read()

if not baseline or not baseline.endswith(b'\n'):
    raise RuntimeError('Baseline journal missing or not newline-terminated')

with open(TARGET, 'wb') as out:
    out.write(baseline)
    out.write(b'{"version":1,"payload_json":"{\\"seq\\":4')
    out.flush()

print('Created dedicated damaged test journal:', TARGET)
print('Original journal left unchanged:', SOURCE)
