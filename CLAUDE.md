# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Raspberry Pi tool that connects directly to the playfield switch harness of early Bally solid-state pinball machines (bypassing the MPU) to test switches, diodes, and wiring. Game-specific switch definitions are loaded from JSON files, making it easy to support additional games. First target: Bally Mata Hari (1978).

## Development Commands

Uses `uv` for package management. `RPi.GPIO` is Linux/ARM-only and will not install on Windows.

```bash
# On the Pi
uv sync
switch-tester games/mata_hari.json

# Or without installing the entry point
uv run -m switchtester.cli games/mata_hari.json
```

No test suite exists yet. Manual testing requires a Raspberry Pi connected to a Bally switch harness.

## Architecture

```
switchtester/tester.py  -- hardware logic (GPIO, scanning, diode test)
switchtester/cli.py     -- interactive commands and main() entry point
games/*.json            -- per-game switch definitions
```

**Key split:** `tester.py` contains no `print` or `input` -- it is pure hardware logic, designed to be importable by a future web UI or other frontends without pulling in the interactive CLI. All user interaction lives in `cli.py`.

### The `game` dict

`load_game(path)` in `tester.py` returns a dict that flows through nearly every function:

```python
{
    "game_name": str,
    "platform": str,
    "num_cols": int,               # derived from JSON max col + 1
    "num_rows": int,               # derived from JSON max row + 1
    "strobe_wires": {int: str},    # col index -> wire colour string
    "return_wires": {int: str},    # row index -> wire colour string
    "switch_map": {(col, row): (sw_num, name)},
}
```

### Scanning

`scan_matrix()` returns a `set` of `(col, row)` tuples. The monitor loop uses set subtraction (`current - prev`, `prev - current`) to detect open/close events.

`diode_scan()` reverses GPIO direction (rows -> outputs, cols -> inputs), drives each row low, and returns a list of `(col, row)` tuples where reverse current flowed (shorted diode). Always restores normal config before returning.

### Adding a new game

Create a JSON file in `games/` following the schema in `games/mata_hari.json`. `num_cols` and `num_rows` are inferred automatically from the max col/row values in the switches list, so larger matrices (e.g. Bally 6803 platform) work without any code changes.

## Hardware Reference

**GPIO pin assignments (BCM numbering), all on even physical header pins:**

| Function | BCM | Phys | J2 pin | J3 pin |
|----------|-----|------|--------|--------|
| Strobe 0 | 14 | 8 | J2-1 | J3-2 |
| Strobe 1 | 15 | 10 | J2-2 | J3-3 |
| Strobe 2 | 18 | 12 | J2-3 | -- |
| Strobe 3 | 24 | 18 | J2-4 | -- |
| Strobe 4 | 23 | 16 | J2-5 | -- |
| Return I0 | 25 | 22 | J2-8 | J3-9 |
| Return I1 | 8 | 24 | J2-9 | J3-10 |
| Return I2 | 7 | 26 | J2-10 | J3-11 |
| Return I3 | 1 | 28 | J2-11 | J3-12 |
| Return I4 | 16 | 38 | J2-12 | J3-13 |
| Return I5 | 12 | 32 | J2-13 | J3-14 |
| Return I6 | 21 | 40 | J2-14 | J3-15 |
| Return I7 | 20 | 36 | J2-15 | J3-16 |

Strobes 0-1 and all Returns need a Y-split to reach both J2 and J3. Strobes 2-4 are J2 only. BCM 1 (pin 28) has a fixed 1.8k pullup on the Pi board but works fine as an input here. J3 key position is pin 4 (KEY). Strobe 3, Return I4, and Return I6 are routed via jumper wires on the underside of the breakout board -- see wiring.md for full board layout.

J2 is a 15-pin 0.100" Molex KK (playfield switches). J3 is a 16-pin 0.100" Molex KK (cabinet switches). Not 0.156" edge connectors. No ground connection to the game is needed.

Switch matrix: 5 columns x 8 rows, active-low strobes and returns, 1N4148 diode in series with each switch (anode toward row), 0.047 uF ceramic disc cap across contacts.

## Planned Features (not yet implemented)

- Cap testing via GPIO edge timing (detect missing/dead 0.047 uF caps)
- Web UI via Flask for viewing matrix state on a phone while under the playfield
- Physical button on Pi to cycle test modes
- Status LED
- JSON definitions for additional games

## Coding Preferences

- Python 3 only (not MicroPython, not Arduino C)
- UTF-8 basic ASCII only -- no smart quotes, em-dashes, or curly quotes
- No emojis
- Metric units, Celsius, prices in NZD
- Admit uncertainty directly rather than speculating
