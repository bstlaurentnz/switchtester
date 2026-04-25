# Switch Tester Breakout Board Wiring - Bally 6803 / Stern M200

Connects the Raspberry Pi GPIO header to the Bally 6803 switch matrix connectors
(CJ3 and CJ4 on the game). Switch matrix: 6 columns (strobes) x 8 rows (returns),
48 switch positions.


## Signal Table

| Function  | BCM | Physical | CJ3    | CJ4    | Wire (CJ4) |
|-----------|-----|----------|--------|--------|------------|
| Strobe 0  | 16  | 36       | CJ3-15 | CJ4-15 | Wht-Red    |
| Strobe 1  | 13  | 33       | CJ3-14 | CJ4-14 | Wht-Blu    |
| Strobe 2  | 12  | 32       | CJ3-13 | CJ4-13 | Wht-Yel    |
| Strobe 3  | 6   | 31       | CJ3-12 | CJ4-12 | Wht-Grn    |
| Strobe 4  | 5   | 29       | CJ3-11 | CJ4-11 | Wht-Brn    |
| Strobe 5  | 14  | 8        | --     | CJ4-1  | Wht-Vio    |
| Return I0 | 7   | 26       | CJ3-10 | CJ4-10 | Red        |
| Return I1 | 8   | 24       | CJ3-9  | CJ4-9  | Blu        |
| Return I2 | 25  | 22       | CJ3-8  | CJ4-8  | Yel        |
| Return I3 | 22  | 15       | CJ3-7  | CJ4-7  | Grn        |
| Return I4 | 24  | 18       | CJ3-6  | KEY    | Wht        |
| Return I5 | 23  | 16       | CJ3-5  | CJ4-4  | Brn        |
| Return I6 | 18  | 12       | CJ3-4  | CJ4-3  | Orn        |
| Return I7 | 15  | 10       | CJ3-2  | CJ4-2  | Blk        |

BCM 5, 6, 22, 13 are on odd physical header pins (29, 31, 15, 33).
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
