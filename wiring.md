# Switch Tester Breakout Board Wiring

## Board Layout

Perfboard: 20 columns x 5 rows, 0.100" pitch

- Row 1: Raspberry Pi even-numbered GPIO header pins (2x20 socket, even side)
- Row 2: (spare)
- Row 3: J2 - 15 pin 0.100" Molex KK (playfield switches)
- Row 4: J3 - 16 pin 0.100" Molex KK (cabinet switches)
- Row 5: (spare)

## Pin Assignments

| Col | Pi Phys | J2 | J3 | Notes |
|-----|---------|----|----|-------|
| 1 | 2 (5V) | -- | -- | |
| 2 | 4 (5V) | -- | -- | |
| 3 | 6 (GND) | -- | J3-1 (self test, nc) | |
| 4 | 8 (BCM 14) | J2-1 Strobe 0 | J3-2 Strobe 0 | direct |
| 5 | 10 (BCM 15) | J2-2 Strobe 1 | J3-3 Strobe 1 | direct |
| 6 | 12 (BCM 18) | J2-3 Strobe 2 | J3-4 KEY | direct (J2 only) |
| 7 | 14 (GND) | J2-4 Strobe 3 | J3-5 blank | jumper to col 9 |
| 8 | 16 (BCM 23) | J2-5 Strobe 4 | J3-6 blank | direct (J2 only) |
| 9 | 18 (BCM 24) | J2-6 KEY | J3-7 blank | Strobe 3 jumper dest |
| 10 | 20 (GND) | J2-7 unused | J3-8 blank | |
| 11 | 22 (BCM 25) | J2-8 Return I0 | J3-9 Return I0 | direct |
| 12 | 24 (BCM 8) | J2-9 Return I1 | J3-10 Return I1 | direct |
| 13 | 26 (BCM 7) | J2-10 Return I2 | J3-11 Return I2 | direct |
| 14 | 28 (BCM 1) | J2-11 Return I3 | J3-12 Return I3 | direct |
| 15 | 30 (GND) | J2-12 Return I4 | J3-13 Return I4 | jumper to col 19 |
| 16 | 32 (BCM 12) | J2-13 Return I5 | J3-14 Return I5 | direct |
| 17 | 34 (GND) | J2-14 Return I6 | J3-15 Return I6 | jumper to col 20 |
| 18 | 36 (BCM 20) | J2-15 Return I7 | J3-16 Return I7 | direct |
| 19 | 38 (BCM 16) | -- | -- | Return I4 jumper dest |
| 20 | 40 (BCM 21) | -- | -- | Return I6 jumper dest |

## Jumper Wires

3 jumper wires on the underside of the perfboard:

1. Col 7 --> col 9: Strobe 3 (2 columns, J2-4 only)
2. Col 15 --> col 19: Return I4 (4 columns, J2-12 and J3-13 soldered together)
3. Col 17 --> col 20: Return I6 (3 columns, J2-14 and J3-15 soldered together)

## GPIO Pin Assignments (for switch_tester.py)

```python
COL_PINS = [14, 15, 18, 24, 23]  # Strobe 0-4
ROW_PINS = [25, 8, 7, 1, 16, 12, 21, 20]  # Return I0-I7
```