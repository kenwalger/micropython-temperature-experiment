# MicroPython learning lab: annotated scripts

These scripts are annotated copies of the **15 uploaded files**, not a new implementation. The original behavior and filenames are retained, except the three uploaded `(2)` suffixes are normalized to their expected names.

## Documentation approach

- Module docstrings explain the experiment and side effects.
- Function docstrings describe the intent of functions that previously lacked them.
- Wiring comments identify the DS18B20 on GPIO4 and DS3231 on GPIO21/22.
- RTC status register comments explain the oscillator-stop flag.
- The historical `rtc_config.py` timestamp is explicitly labeled as stale.

## Type annotations

This first pass deliberately **does not add runtime type annotations** to the tested scripts. Their compatibility with MicroPython 1.29.0 on the user's ESP32 has not been tested, and the priority is preserving observed behavior. After confirming support on the device, we can introduce simple built-in annotations incrementally (for example `def bcd(value: int) -> int:`), and keep richer type information in optional desktop-only stubs.

## Safety

Do not run all scripts indiscriminately: `rtc_set.py` writes the RTC, `archive_journal.py` renames a file, `journal_inject_tail.py` creates a damaged fixture, and journal writers append observations. `journal_activate.py` is intentionally one-time and refuses to overwrite the active pointer. Read each module docstring first.

These scripts passed CPython **syntax parsing only**. Hardware execution and MicroPython annotation compatibility are not yet tested. Diff the scripts against the originals before replacing your working firmware directory.
