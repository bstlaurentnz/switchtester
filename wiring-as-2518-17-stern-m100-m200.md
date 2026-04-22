# Switch Tester Breakout Board Wiring - Bally AS-2518-17 / Stern M100 / M200

Connects the Raspberry Pi GPIO header to the Bally AS-2518-17 switch matrix
connectors (J2 and J3 on the game). Switch matrix: 5 columns (strobes) x 8 rows
(returns), 40 switch positions.

Wire colours in the table below are for Mata Hari (1978), the first supported game.


## Signal Table

| Function  | BCM | Physical | J2    | J3    | Wire (J2)     |
|-----------|-----|----------|-------|-------|---------------|
| Strobe 0  | 14  | 8        | J2-1  | J3-2  | Wht-Red (51)  |
| Strobe 1  | 15  | 10       | J2-2  | J3-3  | Gry-Yel (93)  |
| Strobe 2  | 18  | 12       | J2-3  | KEY   | Wht-Blu (52)  |
| Strobe 3  | 27  | 13*      | J2-4  | --    | Wht-Yel (53)  |
| Strobe 4  | 23  | 16       | J2-5  | --    | Yel-Red (31)  |
| Return I0 | 25  | 22       | J2-8  | J3-9  | Wht-Grn (54)  |
| Return I1 | 8   | 24       | J2-9  | J3-10 | Wht-Brn (56)  |
| Return I2 | 7   | 26       | J2-10 | J3-11 | Wht-Orn (57)  |
| Return I3 | 5   | 29*      | J2-11 | J3-12 | Wht-Blk (58)  |
| Return I4 | 6   | 31*      | J2-12 | J3-13 | Brn (60)      |
| Return I5 | 12  | 32       | J2-13 | J3-14 | Brn-Yel (63)  |
| Return I6 | 19  | 35*      | J2-14 | J3-15 | Brn-Wht (65)  |
| Return I7 | 16  | 36       | J2-15 | J3-16 | Orn (70)      |

BCM 27, 5, 6, 19 are on odd physical header pins (13, 29, 31, 35).
All others are on even physical header pins.


## Connector Notes

**J2** - 15-pin 0.100" Molex KK (playfield switches)

- Pin 6 is the KEY position (no pin in connector).
- Pin 7 is unused (no switch matrix signal).
- Strobes 0-4 on pins 1-5; Returns I0-I7 on pins 8-15.

**J3** - 16-pin 0.100" Molex KK (cabinet switches, Y-split from J2)

- Pin 4 is the KEY position (no pin in connector).
- Pins 1, 5-8 are not connected to any switch matrix signal.
- Strobe 0-1 only on pins 2-3; Returns I0-I7 on pins 9-16.
- Strobes 2-4 have no J3 connection.


## Pi Header Usage

Even-side physical pins used: 8, 10, 12, 16, 22, 24, 26, 32, 36
Odd-side physical pins used: 13, 29, 31, 35


## Wiring diagram

[switchtester-wiring-17.svg](switchtester-wiring-17.svg)


## Platform definitions

platforms/as-2518-17.json and platforms/stern-m200.json contain the BCM pin
arrays and connector labels used by the software.
