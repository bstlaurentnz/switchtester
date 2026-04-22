# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Raspberry Pi tool that connects directly to the playfield switch harness of Bally and Stern
solid-state pinball machines (bypassing the MPU) to test switches, diodes, and wiring.
Game-specific switch definitions are loaded from JSON files.

Supported platforms:
- **Bally AS-2518-17** -- 5x8 matrix, J2 (15-pin) + J3 (16-pin) Molex KK connectors
- **Stern M100 / M200** -- functionally identical to AS-2518-17; uses the same breakout board
  and the same platform JSON (stern-m200.json mirrors as-2518-17.json pin for pin)
- **Bally 6803** -- 6x8 matrix, CJ3 (15-pin) + CJ4 (15-pin) Molex KK connectors

Supported games: Mata Hari (1978), Atlantis (1989). Adding a game requires only a JSON file.


## Development Commands

Uses `uv` for package management. `RPi.GPIO` is Linux/ARM-only and will not install on Windows.

```bash
# On the Pi -- CLI mode
uv sync
switch-tester games/mata_hari.json

# Or without the installed entry point
uv run -m switchtester.cli games/mata_hari.json

# Web UI (runs on port 5000)
switch-tester-web
uv run -m switchtester.web
```

No test suite exists. Manual testing requires a Raspberry Pi connected to a switch harness.


## Architecture

```
switchtester/tester.py  -- hardware logic (GPIO, scanning, diode test)
switchtester/cli.py     -- interactive commands and main() entry point
switchtester/web.py     -- Flask web UI
games/*.json            -- per-game switch definitions
platforms/*.json        -- per-platform GPIO pin assignments
deploy/setup.sh         -- one-shot deployment (captive portal, systemd service)
```

**Key split:** `tester.py` contains no `print` or `input` -- it is pure hardware logic,
importable by both `cli.py` and `web.py` without pulling in either frontend.

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

`scan_matrix()` drives each row (return) low in turn and reads all cols (strobes). With the
diode cathode toward the row, this forward-biases the diode path and pulls the col input low
for any closed switch. Returns a `set` of `(col, row)` tuples; the monitor loop uses set
subtraction (`current - prev`, `prev - current`) to detect open/close events.

`diode_scan()` reverses GPIO direction (cols -> outputs, rows -> inputs), drives each col low,
and returns a list of `(col, row)` tuples where reverse current flowed (shorted diode). Always
restores normal config before returning.

### Web UI

Flask app in `web.py`, served on port 5000. Routes:

| Route | Description |
|-------|-------------|
| `/` | Game selection -- lists all JSON files in the games directory |
| `/game/<slug>` | Dashboard for a game (links to all test modes) |
| `/game/<slug>/list` | All switches with switch number, name, and wire colours |
| `/game/<slug>/snapshot` | One-shot matrix read shown as a grid |
| `/game/<slug>/diode` | Diode test -- lists switches with shorted diodes |
| `/game/<slug>/monitor` | Live monitor via server-sent events (SSE), 50 ms poll |

GPIO is shared between routes via a threading lock. Switching games re-runs `setup_gpio()`.
Walk test, pin continuity, and remap are CLI-only (they require interactive back-and-forth).

### Adding a new game

Create a JSON file in `games/` following the schema in `games/mata_hari.json`. `num_cols`
and `num_rows` are inferred from the max col/row values in the switches list, so a 6x8
matrix (Bally 6803) works without any code changes.


## Deployment (Captive Portal)

`deploy/setup.sh` configures the Pi as a self-contained WiFi access point so a phone or
tablet can use the web UI without a router. Run it once on the Pi:

```bash
bash deploy/setup.sh
```

What it does:

1. Installs `dnsmasq` and `iptables-persistent` if missing
2. Creates a WiFi AP on `wlan0` -- SSID **SwitchTester**, IP `10.42.0.1/24`
3. Configures `dnsmasq` to answer all DNS queries on `wlan0` with `10.42.0.1`
   (captive-portal redirect -- any URL opens the web UI)
4. Adds iptables rules to redirect port 80 and 443 on `wlan0` to Flask on port 5000
5. Installs and enables a systemd service (`switchtester-web`) that runs `switch-tester-web`
   automatically on boot
6. Leaves `eth0` working normally for SSH and internet access from the Pi itself

After setup: connect a phone to **SwitchTester** WiFi, open any URL, and the web UI appears.
The Pi can still be accessed via SSH over Ethernet.


## Hardware Reference

### Bally AS-2518-17 / Stern M100 / Stern M200

Switch matrix: 5 columns x 8 rows (40 switches). Active-low strobes and returns.
1N4148 diode per switch (cathode toward row / anode toward col strobe).
0.047 uF ceramic disc cap across certain contacts.

J2 is a 15-pin 0.100" Molex KK (playfield switches). Pin 6 is KEY.
J3 is a 16-pin 0.100" Molex KK (cabinet switches). Pin 4 is KEY.
No ground connection to the game is needed.

Strobes 0-1 reach both J2 and J3. Strobes 2-4 are J2 only.

| Function  | BCM | Phys | J2    | J3    |
|-----------|-----|------|-------|-------|
| Strobe 0  | 14  | 8    | J2-1  | J3-2  |
| Strobe 1  | 15  | 10   | J2-2  | J3-3  |
| Strobe 2  | 18  | 12   | J2-3  | --    |
| Strobe 3  | 27  | 13*  | J2-4  | --    |
| Strobe 4  | 23  | 16   | J2-5  | --    |
| Return I0 | 25  | 22   | J2-8  | J3-9  |
| Return I1 | 8   | 24   | J2-9  | J3-10 |
| Return I2 | 7   | 26   | J2-10 | J3-11 |
| Return I3 | 5   | 29*  | J2-11 | J3-12 |
| Return I4 | 6   | 31*  | J2-12 | J3-13 |
| Return I5 | 12  | 32   | J2-13 | J3-14 |
| Return I6 | 19  | 35*  | J2-14 | J3-15 |
| Return I7 | 16  | 36   | J2-15 | J3-16 |

\* Odd-side physical header pins (BCM 27, 5, 6, 19).

See [wiring-as-2518-17-stern-m100-m200.md](wiring-as-2518-17-stern-m100-m200.md) for full
board layout and [switchtester-wiring-17.svg](switchtester-wiring-17.svg) for the diagram.


### Bally 6803

Switch matrix: 6 columns x 8 rows (48 switches). Active-low strobes and returns.
1N4148 diode per switch (cathode toward row / anode toward col strobe).

CJ4 is a 15-pin 0.100" Molex KK. Pin 6 is KEY -- Return I4 is inaccessible via CJ4
and must be wired via CJ3-6 instead.
CJ3 is a 15-pin 0.100" Molex KK. Pin 3 is KEY.
No ground connection to the game is needed.

| Function  | BCM | Phys | CJ4    | CJ3    |
|-----------|-----|------|--------|--------|
| Strobe 0  | 16  | 36   | CJ4-15 | CJ3-15 |
| Strobe 1  | 13  | 33*  | CJ4-14 | CJ3-14 |
| Strobe 2  | 12  | 32   | CJ4-13 | CJ3-13 |
| Strobe 3  | 6   | 31*  | CJ4-12 | CJ3-12 |
| Strobe 4  | 5   | 29*  | CJ4-11 | CJ3-11 |
| Strobe 5  | 14  | 8    | CJ4-1  | --     |
| Return I0 | 7   | 26   | CJ4-10 | CJ3-10 |
| Return I1 | 8   | 24   | CJ4-9  | CJ3-9  |
| Return I2 | 25  | 22   | CJ4-8  | CJ3-8  |
| Return I3 | 10  | 19*  | CJ4-7  | CJ3-7  |
| Return I4 | 24  | 18   | KEY    | CJ3-6  |
| Return I5 | 23  | 16   | CJ4-4  | CJ3-5  |
| Return I6 | 18  | 12   | CJ4-3  | CJ3-4  |
| Return I7 | 15  | 10   | CJ4-2  | CJ3-2  |

\* Odd-side physical header pins (BCM 13, 6, 5, 10).
CJ4-5 is unused by the game's switch matrix.

See [wiring-bally-6803.md](wiring-bally-6803.md) for full board layout and
[switchtester-wiring-6803.svg](switchtester-wiring-6803.svg) for the diagram.


## Planned Features (not yet implemented)

- Cap testing via GPIO edge timing (detect missing/dead 0.047 uF caps)
- Physical button on Pi to cycle test modes
- Status LED
- JSON definitions for additional games


## Coding Preferences

- Python 3 only (not MicroPython, not Arduino C)
- UTF-8 basic ASCII only -- no smart quotes, em-dashes, or curly quotes
- No emojis
- Metric units, Celsius, prices in NZD
- Admit uncertainty directly rather than speculating
