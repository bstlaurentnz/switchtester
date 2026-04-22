# Switch Tester Breakout Board Wiring - Bally 6803 / Stern M200

Connects the Raspberry Pi GPIO header to the Bally 6803 switch matrix connectors
(CJ3 and CJ4 on the game). Switch matrix: 6 columns (strobes) x 8 rows (returns),
48 switch positions.


## Signal Table

| Function  | BCM | Physical | CJ4    | CJ3    | Wire (CJ4) |
|-----------|-----|----------|--------|--------|------------|
| Strobe 0  | 16  | 36       | CJ4-15 | CJ3-15 | Wht-Red    |
| Strobe 1  | 13  | 33       | CJ4-14 | CJ3-14 | Wht-Blu    |
| Strobe 2  | 12  | 32       | CJ4-13 | CJ3-13 | Wht-Yel    |
| Strobe 3  | 6   | 31       | CJ4-12 | CJ3-12 | Wht-Grn    |
| Strobe 4  | 5   | 29       | CJ4-11 | CJ3-11 | Wht-Brn    |
| Strobe 5  | 14  | 8        | CJ4-1  | --     | Wht-Vio    |
| Return I0 | 7   | 26       | CJ4-10 | CJ3-10 | Red        |
| Return I1 | 8   | 24       | CJ4-9  | CJ3-9  | Blu        |
| Return I2 | 25  | 22       | CJ4-8  | CJ3-8  | Yel        |
| Return I3 | 10  | 19       | CJ4-7  | CJ3-7  | Grn        |
| Return I4 | 24  | 18       | KEY    | CJ3-6  | Wht        |
| Return I5 | 23  | 16       | CJ4-4  | CJ3-5  | Brn        |
| Return I6 | 18  | 12       | CJ4-3  | CJ3-4  | Orn        |
| Return I7 | 15  | 10       | CJ4-2  | CJ3-2  | Blk        |

BCM 5, 6, 10, 13 are on odd physical header pins (29, 31, 19, 33).
All others are on even physical header pins.


## Connector Notes

**CJ4** - 15-pin 0.100" Molex KK (playfield and cabinet switches)

- Pin 6 is the KEY position (no pin in connector).
- Strobe 0-4 occupy pins 15-11 (high end); Strobe 5 is at pin 1 (low end).
- Return I0-I3 occupy pins 10-7; Return I5-I7 occupy pins 4-2.
- Return I4 (CJ4-6) is blocked by the KEY -- connect via CJ3-6 instead.
- CJ4-5 is unused by the switch matrix (not connected to any signal).

**CJ3** - 15-pin 0.100" Molex KK (cabinet switches)

- Pin 3 is the KEY position (no pin in connector).
- Carries the same signals as CJ4 with these exceptions:
  - Strobe 5 (BCM 14) has no CJ3 connection.
  - Return I4 (BCM 24) is accessible via CJ3-6 ONLY (CJ4-6 is KEY).
  - CJ3-1 is not connected.
- Strobes 0-4 on pins 15-11; Returns I0-I7 on pins 10-9, 8-7, 6, 5-4, 3(KEY), 2.

Both connectors are required. Return I4 can only be reached via CJ3.


## Pi Header Usage

Even-side physical pins used: 8, 10, 12, 16, 18, 22, 24, 26, 32, 36
Odd-side physical pins used: 19, 29, 31, 33


## Wiring diagram

[switchtester-wiring-6803.svg](switchtester-wiring-6803.svg)


## Platform definition

platforms/bally-6803.json contains the BCM pin arrays and connector labels used
by the software.
