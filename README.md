# Wine Storage Telemetry — test scripts

Run from Windows PowerShell, with Miniterm closed:

```powershell
py -m mpremote connect COM5 run firmware/sensor_discover.py
py -m mpremote connect COM5 run firmware/sensor_response.py
```

## Interrupted-write simulation

The original `observations.jsonl` is never modified by these test scripts. First, save an off-device copy:

```powershell
py -m mpremote connect COM5 fs cp :observations.jsonl observations-baseline.jsonl
```

Inspect the original (read-only) using a temporary copy under the test name, or simply inspect the original by changing `PATH` in the inspector to `observations.jsonl`. The default inspector expects `observations-recovery-test.jsonl`.

Create the damaged test journal once:

```powershell
py -m mpremote connect COM5 run firmware/journal_inject_tail.py
py -m mpremote connect COM5 run firmware/journal_recovery_test.py
```

Expected: three valid prefix records, last valid sequence 3, INVALID line 4, append not allowed. The injection script refuses to overwrite an existing test journal. Preserve it as evidence. The inspector never writes to disk.

The production `journal_test.py` should continue refusing appends when validation fails. Do not point it at the damaged test file without deliberate configuration.

## Scope

These scripts test logical validation and controlled malformed tails. They do **not** establish durability under sudden power loss, flash atomicity, or a secure CRC. RTC timestamps are not independently calibrated. `sensor_response.py` produces readings without logging them to persistent storage.
