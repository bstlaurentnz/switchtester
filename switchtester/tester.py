"""
GPIO and switch matrix scanning logic.

Hardware-facing layer: GPIO setup, matrix scan, diode test.
No user interaction here -- all print/input lives in cli.py.
"""

import json
import os
import time

# Populated at runtime by load_platform() via load_game()
COL_PINS = []       # BCM pin numbers for strobes, in order
ROW_PINS = []       # BCM pin numbers for returns, in order
_STROBE_LABELS = [] # J2/J3 connector positions for each strobe
_RETURN_LABELS = [] # J2/J3 connector positions for each return


class _LgpioCompat:
    """Thin RPi.GPIO-compatible wrapper around lgpio, for Pi 5 support."""

    BCM = 11
    OUT = 0
    IN = 1
    HIGH = 1
    LOW = 0
    PUD_UP = 22
    PUD_DOWN = 21

    def __init__(self, lgpio_mod, chip):
        self._lg = lgpio_mod
        self._h = lgpio_mod.gpiochip_open(chip)

    def setmode(self, mode):
        pass

    def setwarnings(self, state):
        pass

    def setup(self, pin, direction, initial=None, pull_up_down=None):
        try:
            self._lg.gpio_free(self._h, pin)
        except Exception:
            pass
        if direction == self.OUT:
            level = 1 if (initial is None or initial == self.HIGH) else 0
            self._lg.gpio_claim_output(self._h, pin, level)
        else:
            flags = 0
            if pull_up_down == self.PUD_UP:
                flags = self._lg.SET_PULL_UP
            elif pull_up_down == self.PUD_DOWN:
                flags = self._lg.SET_PULL_DOWN
            self._lg.gpio_claim_input(self._h, pin, flags)

    def output(self, pin, value):
        self._lg.gpio_write(self._h, pin, 1 if value else 0)

    def input(self, pin):
        return self._lg.gpio_read(self._h, pin)

    def cleanup(self):
        if self._h is not None:
            self._lg.gpiochip_close(self._h)
            self._h = None


def _detect_pi_gpiochip():
    try:
        with open("/proc/device-tree/model") as f:
            model = f.read()
        if "Raspberry Pi 5" in model:
            return 4
    except OSError:
        pass
    return 0


def _load_gpio():
    """Try RPi.GPIO first; fall back to lgpio wrapper on Pi 5."""
    chip = _detect_pi_gpiochip()

    if chip == 0:
        # Pi 1-4: RPi.GPIO works
        try:
            import RPi.GPIO as gpio
            gpio.setmode(gpio.BCM)
            gpio.setwarnings(False)
            return gpio, "RPi.GPIO"
        except (RuntimeError, ImportError):
            pass

    # Pi 5 (chip 4) or RPi.GPIO unavailable: use lgpio
    try:
        import lgpio as _lg # pyright: ignore[reportMissingImports]
        return _LgpioCompat(_lg, chip), f"lgpio (gpiochip{chip})"
    except ImportError:
        pass

    raise RuntimeError(
        "No GPIO library available.\n"
        "On Pi 5: sudo apt install python3-lgpio"
    )


GPIO, GPIO_LIBRARY = _load_gpio()


def load_platform(path):
    """Load pin assignments and connector labels from a platform JSON file."""
    with open(path) as f:
        data = json.load(f)
    COL_PINS[:] = data["col_pins"]
    ROW_PINS[:] = data["row_pins"]
    _STROBE_LABELS[:] = data.get("strobe_labels", [])
    _RETURN_LABELS[:] = data.get("return_labels", [])


def save_platform(path):
    """Write current pin assignments back to the platform file, preserving other fields."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        data = {}
    data["col_pins"] = list(COL_PINS)
    data["row_pins"] = list(ROW_PINS)
    data["strobe_labels"] = list(_STROBE_LABELS)
    data["return_labels"] = list(_RETURN_LABELS)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_game(path):
    with open(path, "r") as f:
        data = json.load(f)

    platform = data.get("platform", "")
    game_dir = os.path.dirname(os.path.abspath(path))
    platform_path = os.path.normpath(
        os.path.join(game_dir, "..", "platforms", f"{platform}.json")
    )
    load_platform(platform_path)

    strobe_wires = {int(k): v for k, v in data.get("strobe_wires", {}).items()}
    return_wires = {int(k): v for k, v in data.get("return_wires", {}).items()}

    switch_map = {}
    for sw in data.get("switches", []):
        switch_map[(sw["col"], sw["row"])] = (sw["num"], sw["name"])

    num_cols = max(sw["col"] for sw in data["switches"]) + 1
    num_rows = max(sw["row"] for sw in data["switches"]) + 1

    return {
        "game_name": data.get("game", "Unknown"),
        "platform": platform,
        "platform_path": platform_path,
        "strobe_wires": strobe_wires,
        "return_wires": return_wires,
        "switch_map": switch_map,
        "num_cols": num_cols,
        "num_rows": num_rows,
    }


def setup_gpio(game):
    """Configure GPIO for normal scanning (rows = outputs/strobe, cols = inputs/sense)."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for i in range(game["num_rows"]):
        GPIO.setup(ROW_PINS[i], GPIO.OUT, initial=GPIO.HIGH)
    for i in range(game["num_cols"]):
        GPIO.setup(COL_PINS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)


def switch_info(game, col, row):
    """Return a formatted string: switch number, name, and wire colours."""
    sw_num, name = game["switch_map"].get((col, row), (0, "Unknown"))
    strobe_wire = game["strobe_wires"].get(col, "?")
    return_wire = game["return_wires"].get(row, "?")
    return (
        f"SW {sw_num:2d} - {name}\n"
        f"         Strobe: {strobe_wire}\n"
        f"         Return: {return_wire}"
    )


def scan_matrix(game):
    """
    Scan all rows and return a set of closed switch positions.

    Drives one row low at a time, reads all cols.
    Returns: set of (col, row) tuples for switches that are closed.
    """
    closed = set()
    for r in range(game["num_rows"]):
        GPIO.output(ROW_PINS[r], GPIO.LOW)
        time.sleep(0.0002)
        for c in range(game["num_cols"]):
            if GPIO.input(COL_PINS[c]) == GPIO.LOW:
                closed.add((c, r))
        GPIO.output(ROW_PINS[r], GPIO.HIGH)
    return closed


def diode_scan(game):
    """
    Reverse bias scan to detect shorted diodes.

    Reconfigures cols as outputs and rows as inputs.
    Drives each col low -- if any row reads low, that diode is shorted.

    Returns: list of (col, row) tuples with shorted diodes.
    Restores normal GPIO config before returning.
    """
    for i in range(game["num_rows"]):
        GPIO.setup(ROW_PINS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for i in range(game["num_cols"]):
        GPIO.setup(COL_PINS[i], GPIO.OUT, initial=GPIO.HIGH)

    shorted = []
    for c in range(game["num_cols"]):
        GPIO.output(COL_PINS[c], GPIO.LOW)
        time.sleep(0.0002)
        for r in range(game["num_rows"]):
            if GPIO.input(ROW_PINS[r]) == GPIO.LOW:
                shorted.append((c, r))
        GPIO.output(COL_PINS[c], GPIO.HIGH)

    setup_gpio(game)
    return shorted


def read_switch(game, col, row):
    """
    Read a single switch. Returns True if closed.

    Drives the row low, reads the col, restores the row.
    """
    GPIO.output(ROW_PINS[row], GPIO.LOW)
    time.sleep(0.001)
    closed = GPIO.input(COL_PINS[col]) == GPIO.LOW
    GPIO.output(ROW_PINS[row], GPIO.HIGH)
    return closed


def pin_label(bcm):
    """Return the connector position label (J2/J3) for a BCM pin based on current mapping."""
    for i, p in enumerate(COL_PINS):
        if p == bcm:
            return _STROBE_LABELS[i] if i < len(_STROBE_LABELS) else f"Strobe {i}"
    for i, p in enumerate(ROW_PINS):
        if p == bcm:
            return _RETURN_LABELS[i] if i < len(_RETURN_LABELS) else f"Return I{i}"
    return f"BCM {bcm} (unassigned)"



def remap_strobe(idx, new_bcm):
    """Assign new_bcm to COL_PINS[idx], swapping with wherever new_bcm currently lives."""
    old_bcm = COL_PINS[idx]
    if old_bcm == new_bcm:
        return
    for i, p in enumerate(COL_PINS):
        if p == new_bcm:
            COL_PINS[i] = old_bcm
            break
    for i, p in enumerate(ROW_PINS):
        if p == new_bcm:
            ROW_PINS[i] = old_bcm
            break
    COL_PINS[idx] = new_bcm


def remap_return(idx, new_bcm):
    """Assign new_bcm to ROW_PINS[idx], swapping with wherever new_bcm currently lives."""
    old_bcm = ROW_PINS[idx]
    if old_bcm == new_bcm:
        return
    for i, p in enumerate(COL_PINS):
        if p == new_bcm:
            COL_PINS[i] = old_bcm
            break
    for i, p in enumerate(ROW_PINS):
        if p == new_bcm:
            ROW_PINS[i] = old_bcm
            break
    ROW_PINS[idx] = new_bcm



def pin_continuity_scan():
    """
    Detect which pairs of GPIO pins are directly connected.

    Drives each pin LOW in turn with all others pulled up.
    Returns a set of frozensets, each containing two connected BCM numbers.
    Leaves all pins as inputs when done; caller must call setup_gpio() to restore.
    """
    all_pins = COL_PINS + ROW_PINS

    for p in all_pins:
        GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    connected = set()
    for i, driven in enumerate(all_pins):
        GPIO.setup(driven, GPIO.OUT, initial=GPIO.LOW)
        time.sleep(0.0002)
        for j, read in enumerate(all_pins):
            if j != i and GPIO.input(read) == GPIO.LOW:
                connected.add(frozenset({driven, read}))
        GPIO.setup(driven, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    return connected
