"""
GPIO and switch matrix scanning logic.

Hardware-facing layer: GPIO setup, matrix scan, diode test.
No user interaction here -- all print/input lives in cli.py.
"""

import json
import time

import RPi.GPIO as GPIO

# BCM GPIO numbers -- must match physical wiring to J2/J3
COL_PINS = [14, 15, 18, 24, 23]        # Strobe 0-4
ROW_PINS = [25, 8, 7, 1, 16, 12, 21, 20]  # Return I0-I7


def load_game(path):
    """Load game definition from a JSON file."""
    with open(path, "r") as f:
        data = json.load(f)

    strobe_wires = {int(k): v for k, v in data.get("strobe_wires", {}).items()}
    return_wires = {int(k): v for k, v in data.get("return_wires", {}).items()}

    switch_map = {}
    for sw in data.get("switches", []):
        switch_map[(sw["col"], sw["row"])] = (sw["num"], sw["name"])

    num_cols = max(sw["col"] for sw in data["switches"]) + 1
    num_rows = max(sw["row"] for sw in data["switches"]) + 1

    return {
        "game_name": data.get("game", "Unknown"),
        "platform": data.get("platform", "Unknown"),
        "strobe_wires": strobe_wires,
        "return_wires": return_wires,
        "switch_map": switch_map,
        "num_cols": num_cols,
        "num_rows": num_rows,
    }


def setup_gpio(game):
    """Configure GPIO for normal scanning (cols = outputs, rows = inputs)."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for i in range(game["num_cols"]):
        GPIO.setup(COL_PINS[i], GPIO.OUT, initial=GPIO.HIGH)
    for i in range(game["num_rows"]):
        GPIO.setup(ROW_PINS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)


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
    Scan all columns and return a set of closed switch positions.

    Drives one column low at a time, reads all rows.
    Returns: set of (col, row) tuples for switches that are closed.
    """
    closed = set()
    for c in range(game["num_cols"]):
        GPIO.output(COL_PINS[c], GPIO.LOW)
        time.sleep(0.0002)
        for r in range(game["num_rows"]):
            if GPIO.input(ROW_PINS[r]) == GPIO.LOW:
                closed.add((c, r))
        GPIO.output(COL_PINS[c], GPIO.HIGH)
    return closed


def diode_scan(game):
    """
    Reverse bias scan to detect shorted diodes.

    Reconfigures rows as outputs and columns as inputs.
    Drives each row low -- if any column reads low, that diode is shorted.

    Returns: list of (col, row) tuples with shorted diodes.
    Restores normal GPIO config before returning.
    """
    for i in range(game["num_cols"]):
        GPIO.setup(COL_PINS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for i in range(game["num_rows"]):
        GPIO.setup(ROW_PINS[i], GPIO.OUT, initial=GPIO.HIGH)

    shorted = []
    for r in range(game["num_rows"]):
        GPIO.output(ROW_PINS[r], GPIO.LOW)
        time.sleep(0.0002)
        for c in range(game["num_cols"]):
            if GPIO.input(COL_PINS[c]) == GPIO.LOW:
                shorted.append((c, r))
        GPIO.output(ROW_PINS[r], GPIO.HIGH)

    # Restore normal scanning config
    for i in range(game["num_cols"]):
        GPIO.setup(COL_PINS[i], GPIO.OUT, initial=GPIO.HIGH)
    for i in range(game["num_rows"]):
        GPIO.setup(ROW_PINS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    return shorted


def read_switch(game, col, row):
    """
    Read a single switch. Returns True if closed.

    Drives the column low, reads the row, restores the column.
    """
    GPIO.output(COL_PINS[col], GPIO.LOW)
    time.sleep(0.001)
    closed = GPIO.input(ROW_PINS[row]) == GPIO.LOW
    GPIO.output(COL_PINS[col], GPIO.HIGH)
    return closed
