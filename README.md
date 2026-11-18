# Wine Storage Telemetry

A practical MicroPython experiment using an ESP32 to observe temperature, associate readings with an external clock, and investigate what survives when data is written, interrupted, and recovered.

The motivation is a home wine-storage area. The larger goal is to collect observations over roughly 30–90 days, including deliberate interruptions, and report what the evidence actually supports. This repository is a learning project and an experimental record, **not** a validated monitoring appliance or a guarantee of data durability.

## Hardware and runtime

| Component | Configuration in this experiment |
| --- | --- |
| Controller | Geekworm ESP32-WROVER board |
| Runtime | MicroPython 1.29.0 |
| Temperature probe | Waterproof DS18B20, OneWire data on **GPIO4** |
| Probe power | 3V3 and GND; terminal adapter supplies the OneWire pull-up resistor |
| Real-time clock | DS3231, I²C address `0x68` |
| RTC wiring | SDA on **GPIO21**, SCL on **GPIO22**, plus 3V3 and GND |
| Host connection | USB serial; `COM5` on the tested Windows machine |

GPIO numbers refer to ESP32 GPIO identifiers, **not** physical header-pin positions. Check the wiring and power requirements of your specific modules before connecting them. Some DS3231 breakout boards have charging circuitry that may be unsuitable for non-rechargeable backup coin cells; verify the board design before installing a battery.

## Getting started

Install `mpremote` in a suitable host Python environment, then discover the connected serial port. The Windows workflow below was tested with this hardware.

**Windows PowerShell:**

```powershell
py -m pip install mpremote
py -m mpremote connect list
py -m mpremote connect COM5 run firmware/sensor_discover.py
py -m mpremote connect COM5 run firmware/sensor_response.py
```

**macOS:**

```bash
python3 -m pip install mpremote
python3 -m mpremote connect list
python3 -m mpremote connect /dev/cu.usbserial-XXXX run firmware/sensor_discover.py
```

**Linux:**

```bash
python3 -m pip install mpremote
python3 -m mpremote connect list
python3 -m mpremote connect /dev/ttyUSB0 run firmware/sensor_discover.py
```

The macOS and Linux port names are **examples, not verified ports**. Use the device reported by `connect list`; on Linux, serial permissions may also need configuration. A virtual environment or `uvx` can avoid modifying a system-managed Python installation.

If you use `uv`, the following commands were **verified on Windows** with the ESP32 connected on `COM5`:

```powershell
uvx mpremote connect list
uvx mpremote connect COM5 run firmware/sensor_discover.py
```

The discovery script found one DS18B20 with ROM identifier `287eeed100000063`. The separately tested annotated temperature-reading example returned **17.5 °C** on MicroPython 1.29.0. These are observations from one setup, not guaranteed outputs for other hardware.

`mpremote run` executes a local script on the device; it does not install that script as a boot program. Close any serial monitor using the port before connecting.

## Experiment sequence

The scripts are small, separate investigations rather than one continuously deployed application.

1. **Discover and read the sensor:** `sensor_discover.py`, `sensor_response.py`, and `temperature_read_test.py` explore OneWire identification, conversion delays, and reading validation.
2. **Inspect and initialize the clock:** `rtc_inspect.py`, `rtc_set.py`, and `rtc_verify.py` explore I²C discovery, calendar-register values, and the DS3231 oscillator-stop flag. **Do not rerun clock-setting scripts casually**; they change the clock state.
3. **Combine an observation:** `observation_test.py` records the temperature, sensor identifier, clock status, and timestamp basis. `rtc_after_conversion` means the RTC was read *after* the temperature conversion, not at the exact physical sampling instant.
4. **Investigate storage and recovery:** The journal and recovery scripts explore serialized JSONL observations, checksums, incomplete lines, and generation-based continuation. These experiments are still being developed; review each script's effects before running it.

Example observation shape (from the experiment):

```json
{
  "read_at_utc": "2026-11-18T19:45:29Z",
  "timestamp_basis": "rtc_after_conversion",
  "rtc_osf": false,
  "sensor_rom": "287eeed100000063",
  "temperature_c": 19.5
}
```

A plausible timestamp and a clear oscillator-stop flag do not independently establish clock accuracy.

## Interrupted-write simulation

**These commands are for a controlled test fixture, not the primary journal.** Read the scripts and preserve existing device data before running any file-writing experiment. The original `observations.jsonl` is not modified by the *test scripts described here*, but other scripts in the repository may write state.

First, save an off-device copy of the original journal, if it exists:

```powershell
py -m mpremote connect COM5 fs cp :observations.jsonl observations-baseline.jsonl
```

Inspect the original read-only using a temporary copy under the test name, or inspect the original by changing `PATH` in the inspector to `observations.jsonl`. The default inspector expects `observations-recovery-test.jsonl`.

Create and inspect the damaged test journal **once**:

```powershell
py -m mpremote connect COM5 run firmware/journal_inject_tail.py
py -m mpremote connect COM5 run firmware/journal_recovery_test.py
```

Expected result for this controlled fixture: **three valid prefix records, last valid sequence 3, invalid line 4, and append not allowed**. The injection script refuses to overwrite an existing test journal. Preserve the damaged file as evidence; the inspector is read-only.

The journal writer should refuse to append when validation fails. Do not point it at a damaged test file without deliberate configuration. Recovery and generation-activation scripts can change device files; they are **not** part of the beginner setup steps.

## What the experiment does not establish

- An ice-bath reading is a plausibility check, **not sensor calibration**.
- The RTC's oscillator-stop flag is evidence of a possible interruption, **not proof of absolute clock accuracy**.
- CRC32 can detect some accidental corruption; it is **not authentication or tamper resistance**.
- A deliberately truncated JSONL line tests logical validation; it does **not** establish sudden-power-loss durability, flash atomicity, or crash-atomic recovery.
- Successful execution after a software reset is **not** the same as a test involving unexpected loss of power.
- macOS and Linux command examples have not been tested on the physical setup used here.

The longer-duration run and microSD comparisons will be documented only as they are performed.

## Writing and references

This project accompanies the article series **Revisiting MicroPython in the Real World**. The first article revisits MicroPython through GPIO, OneWire, I²C, and the meaning of a timestamp. The next installment will focus on storage and recovery.

<!-- Add the published article URL and a stable post-01 tag/release URL when available. -->

## License

MIT License can be found [here](LICENSE).