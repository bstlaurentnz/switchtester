# Switch Tester

Raspberry Pi tool for testing the switch matrix on Bally and Stern solid-state pinball
machines. Connects directly to the playfield switch harness, bypassing the MPU, to test
switches, diodes, and wiring continuity. The machine does not need to be powered on.

Supported platforms:

| Platform | Matrix | Games |
|----------|--------|-------|
| Bally AS-2518-17 | 5x8 | Mata Hari (1978) |
| Stern M100 / M200 | 5x8 | (same board as AS-2518-17) |
| Bally 6803 | 6x8 | Atlantis (1989) |


## Hardware

A breakout board bridges the Raspberry Pi GPIO header to the game's switch connectors
(Molex KK 0.100"). No ground connection to the game is needed. The machine can remain
completely powered off.

GPIO pin assignments and connector positions for each platform are defined in
`platforms/*.json`. See the wiring documents for board layout:

- [wiring-as-2518-17-stern-m100-m200.md](wiring-as-2518-17-stern-m100-m200.md)
- [wiring-bally-6803.md](wiring-bally-6803.md)


## Setup

Requires a Raspberry Pi running Linux with the `uv` package manager installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repo and install dependencies:

```bash
uv sync
```

`RPi.GPIO` is Linux/ARM only and will not install on other platforms.


## Web UI (recommended)

The web interface runs on the Pi and lets you use a phone or tablet to view the switch
matrix while you are physically under the playfield -- no laptop needed.

### Captive portal deployment

Run the setup script once. It installs and configures everything:

```bash
bash deploy/setup.sh
```

What it sets up:

- WiFi access point on `wlan0` -- SSID **SwitchTester**, no password
- Captive portal: any URL typed in a browser on that network opens the web UI
- HTTP/HTTPS traffic redirected to Flask on port 5000 via iptables
- `switchtester-web` systemd service starts automatically on boot
- Ethernet (`eth0`) is left unchanged -- SSH access over the network still works

After setup: connect your phone to **SwitchTester**, open any URL, and the web UI appears.
The Pi can still be reached via SSH over Ethernet.

### Web UI pages

| Page | What it shows |
|------|---------------|
| List | All switches with number, name, and wire colours |
| Snapshot | One-shot read of the full matrix as a grid, which refreshes every second|
| Diode test | Lists any switches with shorted diodes |
| Monitor | Live view -- updates in real time as switches open and close |


## Connecting to the pinball machine

Unplug the switch harness connectors (J2/J3 for AS-2518-17, CJ3/CJ4 for 6803) and
plug them into the breakout board. Power the Pi from USB.

**The pinball machine does not need to be on. Connecting while it is on is not recommended.**

For AS-2518-17 and Stern: J2 is 15 pins (playfield), J3 is 16 pins (cabinet).
For Bally 6803: CJ4 is 15 pins (main), CJ3 is 15 pins (cabinet). Both are required
because CJ4 pin 6 is the KEY position -- Return I4 is only accessible via CJ3.


## CLI usage (alternative)

The command-line interface is useful for advanced operations like pin remapping.
It requires an SSH session on the Pi.

```bash
switch-tester games/mata_hari.json

# Or without the installed entry point
uv run -m switchtester.cli games/mata_hari.json
```

### Commands

| Key | Command |
|-----|---------|
| `m` | Monitor mode -- continuous scan, reports switch open/close events |
| `d` | Diode reverse bias test -- detects shorted diodes |
| `w` | Walk test -- guided switch-by-switch verification |
| `s` | Snapshot -- current matrix state as a table |
| `l` | List all switches with wire colours |
| `p` | Pin continuity -- connect a jumper to identify which two pins are shorted |
| `r` | Remap pins -- guided verification and correction of GPIO-to-connector wiring |
| `q` | Quit |

### Pin remapper

Run `r` at least once on a new board to confirm all pins are wired correctly.

The remapper walks through each strobe and return pin. Connect a jumper wire between
the pin under test and any other GPIO pin, then press Enter. The Pi detects which BCM
pair is shorted and confirms it matches the expected connector position. On a mismatch
it offers to swap the assignments and saves corrections back to the platform JSON.

This is super useful if you've realised you've miswired the breakout board and don't want to redo the whole thing.

### Pin continuity

Another useful way to test the breakoutboard once built before you plug into the pinball machine, this one tells you which two pins are connected, using the connector's names for them (e.g. J3-1). 

## Adding a game

Create a JSON file in `games/` following the structure of `games/mata_hari.json`. Set
`"platform"` to the name of a file in `platforms/`. `num_cols` and `num_rows` are
inferred automatically from the switch list.

## Adding a platform

Create a JSON file in `platforms/`:

```json
{
    "platform": "my-platform",
    "description": "...",
    "col_pins": [...],
    "row_pins": [...],
    "strobe_labels": [...],
    "return_labels": [...]
}
```

Then set `"platform": "my-platform"` in any game JSON that uses it.
