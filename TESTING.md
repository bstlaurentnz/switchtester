# Switch Tester Test Plan

Target game: Bally Mata Hari (1978), AS-2518-17 platform.

All tests assume the breakout board is connected to the Pi and the J2/J3 harness
is unplugged from the MPU. The machine does not need to be powered -- the tester
supplies its own logic levels via the Pi GPIO.

---

## 1. Physical Setup

1. Power off the machine completely.
2. Disconnect J2 (15-pin, playfield switches) and J3 (16-pin, cabinet switches)
   from the MPU board.
3. Plug J2 and J3 into the breakout board.
4. Confirm the Pi is powered and `uv sync` has been run.

---

## 2. Switch List (no GPIO required)

```
switch-tester games/mata_hari.json
> l
```

**Expected:** 40 switches listed in order SW1-SW40, each with correct strobe
and return wire colours matching the Mata Hari schematics.

Spot-check a few:

| SW | Name | Strobe | Return |
|----|------|--------|--------|
| 6 | Credit Button | Wht-Red (51) / Red-Yel (13) | Brn-Yel (63) / Blu-Wht (25) |
| 32 | Top Saucer | Wht-Yel (53) | Orn (70) / Yel (30) |
| 37 | Bottom Right Thumper Bumper | Yel-Red (31) | Brn (60) / Blu-Yel (23) |

---

## 3. Snapshot

```
switch-tester games/mata_hari.json
> s
```

**Expected with no switches held:**
All cells show open. Confirm the grid is 5 columns x 8 rows.

**Expected with a switch held closed:**
Manually hold down the Credit Button (SW6). Re-run snapshot.
SW6 (col 0, row 5) should appear as closed. Release and snapshot again -- open.

---

## 4. Monitor Mode

```
switch-tester games/mata_hari.json
> m
```

Work through the playfield, activating each accessible switch by hand.
For each switch:

- Press and hold -- a CLOSED event should appear immediately (within ~20 ms).
- Release -- an OPENED event should appear.
- No phantom closures or missed events.

**Suggested sequence:**
1. Credit Button (SW6) -- easy access, cabinet front
2. Outhole (SW8) -- drop a ball into the outhole by hand
3. Right and Left Flipper Feeder Lanes (SW25, SW26)
4. Right Slingshot / Left Slingshot (SW35, SW36) -- press the rubber by hand
5. All four Thumper Bumpers (SW37-SW40) -- press each ring down
6. Top Saucer (SW32) -- drop a ball in
7. Right Drop Targets D-A (SW17-SW20) -- push each target down
8. Left Drop Targets D-A (SW21-SW24) -- push each target down
9. Top 'A' and 'B' Lanes (SW30, SW31), Right/Left 'B'/'A' Lanes (SW28, SW29)
10. Right / Left Outlane (SW33, SW34)

**Pass criteria:** Every switch reports CLOSED on press and OPENED on release,
with no spurious events between presses.

---

## 5. Diode Test

```
switch-tester games/mata_hari.json
> d
```

**Expected:** "No shorted diodes found."

If any diode is reported shorted, note the switch number and wire colours.
Verify physically: measure the diode in-circuit with a multimeter on diode mode.
A healthy 1N4148 reads ~0.6 V forward, OL reverse. A shorted diode reads near
0 V in both directions.

---

## 6. Web UI

Start the web server:

```
switch-tester-web
```

Open `http://<pi-ip>:5000` on a phone. The Pi's IP can be found with `hostname -I`.

### 6a. Game Selection

- Mata Hari should appear in the game list.
- Tapping it loads the dashboard with four mode buttons.

### 6b. Switch List (web)

- Tap "Switch List".
- Confirm all 40 switches are shown with correct wire colours.

### 6c. Snapshot (web)

- Tap "Snapshot".
- Hold the Credit Button (SW6) closed -- its cell should highlight green within 1 second.
- Release -- cell returns to dark on the next refresh.

### 6d. Monitor (web)

- Tap "Monitor". Status line should read "Live".
- Press and release several switches.
- Each should log a CLOSED and OPENED event with a timestamp.
- Press 10+ switches rapidly -- confirm no events are dropped or duplicated.

### 6e. Diode Test (web)

- Tap "Diode Test".
- Expected: "No shorted diodes found."
- Tap "Run Again" -- result should be consistent.

---

## 7. Stress / Edge Cases

- **Simultaneous switches:** Hold two switches in the same row and confirm both
  appear closed in snapshot and monitor.
- **Reconnect monitor:** With monitor open in the browser, navigate away and
  return. The SSE stream should reconnect and resume.
- **Game switch:** Navigate back to the game list and re-select Mata Hari.
  GPIO should reinitialise cleanly with no errors.

---

## Known Limitations

- Walk test, pin continuity, and remap are CLI-only and not covered here.
- SW1-SW5, SW12-SW15 are listed as "Not Used" in Mata Hari -- no physical
  switch to activate. Their absence from all test results is expected.
- Coin chute switches (SW9-SW11) require coins or a jumper wire to test.
- Slam tilt (SW16) and tilt (SW7) can be tested by briefly shorting the
  switch terminals with a screwdriver.
