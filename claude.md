# Bally -17 Switch Matrix Tester

## Project Overview

A Raspberry Pi-based playfield switch matrix tester for early Bally solid-state pinball machines (-17 platform). The tester connects directly to the playfield switch harness (disconnected from the MPU) and scans the switch matrix to detect switch closures, shorted diodes, and open diodes. The first target game is the Bally Mata Hari (1978).

The tester is generic: game-specific switch definitions (names, wire colours, matrix positions) are loaded from a JSON file passed as a command line argument. New games can be supported by creating a new JSON file.

## Hardware

### Platform
- Raspberry Pi 4 or 5 (any model works, Pi Zero would also be fine)
- Powered from a USB-C battery pack (needs 2-3A capable, watch for low-current shutoff on cheap packs)
- No level shifting required -- 3.3V GPIO is sufficient for testing switches and diodes (we are not interfacing with the MPU, just testing passive switch/diode/cap circuits)
- No ground connection to the game is needed -- the Pi sources pullups and sinks strobes through its own GPIOs, forming a complete circuit internally

### Connectors
- J2: 15-pin 0.100" (2.54mm) Molex KK connector on the MPU board (playfield switches)
- J3: 16-pin 0.100" (2.54mm) Molex KK connector on the MPU board (cabinet switches)
- These are NOT 0.156" edge connectors
- The tester connects to the playfield harness side of J2 and J3 (i.e. the harness that normally plugs into the MPU)
- J3 key position is unknown -- check the physical harness or manual wiring diagram

### GPIO Pin Assignments

All pins are on even-numbered physical pins (one row of the header) for cleaner wiring.

| Function | BCM GPIO | Pi Phys Pin | J2 Pin | J2 Wire | J3 Pin | J3 Wire |
|----------|----------|-------------|--------|---------|--------|---------|
| Strobe 0 | 14 | 8 | J2-1 | Wht-Red (51) | J3-2 | Red-Yel (13) |
| Strobe 1 | 15 | 10 | J2-2 | Gry-Yel (93) | J3-3 | Red-Grn (14) |
| Strobe 2 | 18 | 12 | J2-3 | Wht-Blu (52) | -- | -- |
| Strobe 3 | 23 | 16 | J2-4 | Wht-Yel (53) | -- | -- |
| Strobe 4 | 24 | 18 | J2-5 | Yel-Red (31) | -- | -- |
| Return I0 | 25 | 22 | J2-8 | Wht-Grn (54) | J3-9 | Red-Wht (15) |
| Return I1 | 8 | 24 | J2-9 | Wht-Brn (56) | J3-10 | Brn-Wht (65) |
| Return I2 | 7 | 26 | J2-10 | Wht-Orn (57) | J3-11 | Blu (20) |
| Return I3 | 1 | 28 | J2-11 | Wht-Blk (58) | J3-12 | Blu-Red (21) |
| Return I4 | 12 | 32 | J2-12 | Brn (60) | J3-13 | Blu-Yel (23) |
| Return I5 | 16 | 36 | J2-13 | Brn-Yel (63) | J3-14 | Blu-Wht (25) |
| Return I6 | 20 | 38 | J2-14 | Brn-Wht (65) | J3-15 | Blu-Orn (27) |
| Return I7 | 21 | 40 | J2-15 | Orn (70) | J3-16 | Yel (30) |

- 13 GPIO pins total
- 10 of them (Strobes 0-1 and all 8 Returns) need a Y-split to reach both J2 and J3
- 3 (Strobes 2-4) only go to J2
- BCM 1 (physical pin 28) is normally reserved for HAT EEPROM ID_SC and has a fixed 1.8k pullup to 3.3V on the board. Works fine as a GPIO input for this use case.

### Switch Matrix Basics (Bally -17)

- 5 columns (strobes, active-low) x 8 rows (returns, active-low)
- 40 switch positions total
- Each switch has a 1N4148 diode in series (current flows column to row when column is driven low)
- Each switch has a 0.047 uF ceramic disc capacitor across the contacts for debouncing
- The MPU scans by driving one column low at a time and reading all 8 rows

## Software

### Language and Framework
- Python 3 with RPi.GPIO
- Game definitions loaded from JSON files
- Script is invoked as: `python3 switch_tester.py <game_definition.json>`

### Current Features
- **Monitor mode (m)**: Continuous scan reporting switch open/close events with switch names and wire colours
- **Diode test (d)**: Reverse bias test -- reconfigures rows as outputs and columns as inputs, drives each row low, checks if any column reads low (indicating a shorted diode). A good diode blocks reverse current at any voltage.
- **Walk test (w)**: Guided switch-by-switch test prompting the user to close each switch and verifying detection
- **Snapshot (s)**: Prints current matrix state as a table showing which switches are closed
- **List switches (l)**: Dumps all switches with wire colours for reference

### JSON Game Definition Format

```json
{
    "game": "Bally Mata Hari",
    "platform": "-17",
    "strobe_wires": {
        "0": "Wht-Red (51) / Red-Yel (13)",
        ...
    },
    "return_wires": {
        "0": "Wht-Grn (54) / Red-Wht (15)",
        ...
    },
    "switches": [
        {"col": 0, "row": 0, "num": 1, "name": "Not Used"},
        {"col": 0, "row": 5, "num": 6, "name": "Credit Button"},
        ...
    ]
}
```

The script derives matrix dimensions (num_cols, num_rows) from the JSON automatically, so it will handle larger matrices (e.g. 6803 platform) if a JSON file is created for one.

### Pin Configuration in Script

```python
COL_PINS = [14, 15, 18, 23, 24]  # Strobe 0-4
ROW_PINS = [25, 8, 7, 1, 12, 16, 20, 21]  # Return I0-I7
```

### How the Tests Work

**Normal scan**: Drive one column GPIO low, all others high. Read 8 row GPIOs. If a row reads low, the switch at that intersection is closed (current flows through the diode from column to row). Internal pullups on the row GPIOs hold them high when no switch is closed.

**Diode reverse bias test**: Swap directions -- configure columns as inputs with pullups, rows as outputs. Drive each row low and check if any column reads low. Current should NOT flow backwards through a good 1N4148 (reverse breakdown is 100V). If a column reads low, that diode is shorted. Restore normal config after test.

**Cap testing (not yet implemented)**: Could detect missing/dead caps by measuring rise/fall time of row signals when a switch opens/closes. A missing cap means sharper edges (no RC smoothing). Could use GPIO edge timing or ADC if available.

## Files

- `switch_tester.py` -- main script
- `mata_hari.json` -- Mata Hari game definition

## Existing Commercial Testers (for reference)

- Pinitech 64 Switch Matrix Tester -- tests from the MPU side (simulates switch closures), not from the playfield side
- Pinitech had a playfield switch tester but it appears discontinued (archived links)
- Siegecraft makes switch/lamp/solenoid testers
- FIX-IT tester (Game Boards USA) -- diagnostic ROM module for Bally MPUs
- MARCO test ROMs -- diagnostic ROMs for bench-testing Bally MPU boards

## Future Considerations

- Add cap testing (edge timing analysis)
- Web UI via Flask for viewing matrix state on phone while under the playfield
- Create JSON definitions for other games (e.g. Bally Atlantis on 6803 platform -- larger matrix)
- Physical button on the tester to cycle through test modes without needing a keyboard
- Status LED for basic feedback
- Consider a breakout board (perfboard with 0.100" KK headers for J2/J3 on one side and 2x20 pin socket for Pi header on the other)

## Coding Preferences

- Python 3 (not MicroPython, not Arduino C)
- UTF-8 basic characters only -- no smart quotes, em-dashes, curly quotes, or extended characters
- No emojis
- Metric units and Celsius
- Prices in NZD
- Admit uncertainty directly rather than speculating