# Switch Tester Breakout Board Wiring - Bally 6803

## Board Layout

Perfboard: 20 columns x 5 rows, 0.100" pitch

- Row 1: Raspberry Pi even-numbered GPIO header pins (2x20 socket, even side)
- Row 2: (spare) - leaves room to solder jumpers
- Row 3: J4 (CJ4) - 15-pin 0.100" Molex KK, CJ4-15 at col 4
- Row 4: (spare) - leaves room to solder jumpers
- Row 5: (unused - no second connector needed for 6803)

All 14 switch matrix signals (6 strobes + 8 returns) are present on the single
J4 (CJ4) connector. No J3 connector is needed.

CJ4 pin 5 is the KEY position (physically absent from the connector).
ST5 (CJ4-1) is at the opposite end of the connector from ST0-ST4 (CJ4-15 to 11),
with the 8 return lines between them.


## Signal Table

| Function  | BCM | Physical | CJ4   | Wire         |
|-----------|-----|----------|-------|--------------|
| Strobe 0  | 14  | 8        | CJ4-15 | Wht-Red     |
| Strobe 1  | 15  | 10       | CJ4-14 | Wht-Blu     |
| Strobe 2  | 18  | 12       | CJ4-13 | Wht-Yel     |
| Strobe 3  | 22  | 15*      | CJ4-12 | Wht-Orn     |
| Strobe 4  | 23  | 16       | CJ4-11 | Wht-Brn     |
| Strobe 5  | 20  | 36       | CJ4-1  | Wht-Vio     |
| Return I0 | 24  | 18       | CJ4-10 | Red         |
| Return I1 | 1   | 28       | CJ4-9  | Blu         |
| Return I2 | 25  | 22       | CJ4-8  | Yel         |
| Return I3 | 8   | 24       | CJ4-7  | Grn         |
| Return I4 | 7   | 26       | CJ4-6  | Wht         |
| Return I5 | 16  | 38       | CJ4-4  | Brn         |
| Return I6 | 12  | 32       | CJ4-3  | Orn         |
| Return I7 | 21  | 40       | CJ4-2  | Blk         |

*Physical pin 15 is an odd pin. All other signals use even physical pins.
CJ4-5 is the KEY position (no pin in connector, aligns with BCM 1 column).


## Pin Assignments

| Col | Pi Phys      | CJ4 Pin | Notes                                |
|-----|--------------|---------|--------------------------------------|
| 1   | 2 (5V)       | --      |                                      |
| 2   | 4 (5V)       | --      |                                      |
| 3   | 6 (GND)      | --      |                                      |
| 4   | 8 (BCM 14)   | CJ4-15 Strobe 0  | direct                    |
| 5   | 10 (BCM 15)  | CJ4-14 Strobe 1  | direct                    |
| 6   | 12 (BCM 18)  | CJ4-13 Strobe 2  | direct                    |
| 7   | 14 (GND)     | CJ4-12 Strobe 3  | wire to phys pin 15 (BCM 22) |
| 8   | 16 (BCM 23)  | CJ4-11 Strobe 4  | direct                    |
| 9   | 18 (BCM 24)  | CJ4-10 Return I0 | direct                    |
| 10  | 20 (GND)     | CJ4-9 Return I1  | jumper to col 14 (BCM 1)  |
| 11  | 22 (BCM 25)  | CJ4-8 Return I2  | direct                    |
| 12  | 24 (BCM 8)   | CJ4-7 Return I3  | direct                    |
| 13  | 26 (BCM 7)   | CJ4-6 Return I4  | direct                    |
| 14  | 28 (BCM 1)   | CJ4-5 KEY        | Return I1 jumper dest; no J4 pad |
| 15  | 30 (GND)     | CJ4-4 Return I5  | jumper to col 19 (BCM 16) |
| 16  | 32 (BCM 12)  | CJ4-3 Return I6  | direct                    |
| 17  | 34 (GND)     | CJ4-2 Return I7  | jumper to col 20 (BCM 21) |
| 18  | 36 (BCM 20)  | CJ4-1 Strobe 5   | direct                    |
| 19  | 38 (BCM 16)  | --      | Return I5 jumper dest                |
| 20  | 40 (BCM 21)  | --      | Return I7 jumper dest                |


## Jumper Wires

4 connections required (vs 3 on the AS-2518-17 board):

1. Col 7 --> physical pin 15 (BCM 22, odd side of header): Strobe 3 -- short wire,
   pin 15 is immediately adjacent to col 7 (physical pins 14 and 16)
2. Col 10 --> col 14: Return I1 (4 columns)
3. Col 15 --> col 19: Return I5 (4 columns)
4. Col 17 --> col 20: Return I7 (3 columns)


## Board Diagram

```
Col:  01   02   03   04   05   06   07   08   09   10   11   12   13   14   15   16   17   18   19   20
     +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
ODD  |3.3V|BCM2|BCM3|BCM4| GND|B17 |B27 |B22*|3.3V|B10 |BCM9|B11 | GND|BCM0|BCM5|BCM6|B13 |B19 |B26 | GND|
phys  (1)  (3)  (5)  (7)  (9) (11) (13) (15) (17) (19) (21) (23) (25) (27) (29) (31) (33) (35) (37) (39)
     +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
EVEN | 5V | 5V |GND | 14 | 15 | 18 |GND | 23 | 24 |GND | 25 |  8 |  7 |  1 |GND | 12 |GND | 20 | 16 | 21 |
phys  (2)  (4)  (6)  (8) (10) (12) (14) (16) (18) (20) (22) (24) (26) (28) (30) (32) (34) (36) (38) (40)
     +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+

     (spare row 2 -- jumper routing)

     +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
CJ4  |    |    |    | 15 | 14 | 13 | 12 | 11 | 10 |  9 |  8 |  7 |  6 |KEY |  4 |  3 |  2 |  1 |    |    |
sig  |    |    |    | S0 | S1 | S2 | S3 | S4 | R0 | R1 | R2 | R3 | R4 |    | R5 | R6 | R7 | S5 |    |    |
     +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
conn                   =    =    =    J    =    =    J    =    =    =    J         J    =    J    =

Direct connections (even Pi pin to CJ4, same column):
  04: BCM14->C15(S0)  05: BCM15->C14(S1)  06: BCM18->C13(S2)  08: BCM23->C11(S4)
  09: BCM24->C10(R0)  11: BCM25->C8(R2)   12: BCM8->C7(R3)    13: BCM7->C6(R4)
  16: BCM12->C3(R6)   18: BCM20->C1(S5)

Jumpers (J):
  J1  col 7  -> odd-side pin 15 (BCM22*)    S3  [short wire, pin 15 is adjacent to col 7]
  J2  col 10 -> col 14 (BCM1)               R1  [4-col wire]
  J3  col 15 -> col 19 (BCM16)              R5  [4-col wire]
  J4  col 17 -> col 20 (BCM21)              R7  [3-col wire]

* BCM22 (phys pin 15) is the only odd-side pin used.
```


## Pin definition

platforms/bally-6803.json contains all the data needed to support the 6803 J4 connector.
