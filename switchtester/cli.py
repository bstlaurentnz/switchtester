"""
Interactive CLI for the switch matrix tester.

All user-facing commands live here. Hardware logic is in tester.py.
"""

import sys
import time

import RPi.GPIO as GPIO

from .tester import (
    diode_scan,
    load_game,
    read_switch,
    scan_matrix,
    setup_gpio,
    switch_info,
)


def cmd_monitor(game):
    """Continuous scan, reporting switch open/close events."""
    print("Monitoring... Ctrl+C to stop\n")
    prev = set()
    try:
        while True:
            current = scan_matrix(game)

            for key in current - prev:
                c, r = key
                print(f"CLOSED: {switch_info(game, c, r)}")

            for key in prev - current:
                c, r = key
                sw_num, name = game["switch_map"].get(key, (0, "Unknown"))
                print(f"OPENED: SW {sw_num} - {name}")

            prev = current
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nStopped monitoring\n")


def cmd_diode_test(game):
    """Reverse bias test to detect shorted diodes."""
    print("\n--- Diode reverse bias test ---")
    shorted = diode_scan(game)
    if shorted:
        for c, r in shorted:
            print(f"  SHORTED DIODE: {switch_info(game, c, r)}")
    else:
        print("  All diodes OK")
    print("--- Diode test complete ---\n")


def cmd_walk_test(game):
    """Guided switch-by-switch test. Prompts user to close each switch."""
    print("\n--- Full switch walk test ---")
    print("Close each switch when prompted, press Enter to skip\n")

    for c in range(game["num_cols"]):
        for r in range(game["num_rows"]):
            sw_num, name = game["switch_map"].get((c, r), (0, "Unknown"))
            if "Not Used" in name:
                continue

            strobe_wire = game["strobe_wires"].get(c, "?")
            return_wire = game["return_wires"].get(r, "?")
            print(f"SW {sw_num} - {name}")
            print(f"  Strobe: {strobe_wire}")
            print(f"  Return: {return_wire}")
            input("  Close switch and press Enter...")

            if read_switch(game, c, r):
                print(f"  OK: SW {sw_num} detected\n")
            else:
                print(f"  FAIL: SW {sw_num} not detected - check wiring/diode\n")

    print("--- Walk test complete ---\n")


def cmd_snapshot(game):
    """Print current matrix state as a table."""
    print("\n--- Current matrix state ---\n")
    current = scan_matrix(game)

    header = f"{'':20s}"
    for c in range(game["num_cols"]):
        header += f"  ST{c}  "
    print(header)
    print("-" * len(header))

    for r in range(game["num_rows"]):
        line = f"{'Return I' + str(r):20s}"
        for c in range(game["num_cols"]):
            sw_num, _ = game["switch_map"].get((c, r), (0, "?"))
            if (c, r) in current:
                line += f" [{sw_num:2d}]  "
            else:
                line += f"  {sw_num:2d}   "
        print(line)

    print("\n[] = closed switch\n")


def cmd_list_switches(game):
    """Print all switches with wire colours."""
    print(f"\n--- {game['game_name']} switch list ---\n")
    switches = sorted(game["switch_map"].items(), key=lambda x: x[1][0])
    for (c, r), (sw_num, name) in switches:
        if "Not Used" in name:
            continue
        print(f"SW {sw_num:2d} - {name}")
        print(f"       Strobe {c}: {game['strobe_wires'].get(c, '?')}")
        print(f"       Return {r}: {game['return_wires'].get(r, '?')}")
        print()
    print("--- End of switch list ---\n")


COMMANDS = {
    "m": ("monitor mode (continuous scan)", cmd_monitor),
    "d": ("diode reverse bias test", cmd_diode_test),
    "w": ("walk test (guided switch-by-switch)", cmd_walk_test),
    "s": ("snapshot matrix state", cmd_snapshot),
    "l": ("list all switches with wire colours", cmd_list_switches),
    "q": ("quit", None),
}


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <game_definition.json>")
        sys.exit(1)

    game = load_game(sys.argv[1])
    setup_gpio(game)

    print(f"{game['game_name']} ({game['platform']}) Switch Matrix Tester")
    print("=" * 50)
    print(f"Matrix: {game['num_cols']} columns x {game['num_rows']} rows")
    print()
    print("Commands:")
    for key, (description, _) in COMMANDS.items():
        print(f"  {key} = {description}")
    print()

    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == "q":
                break
            entry = COMMANDS.get(cmd)
            if entry:
                _, fn = entry
                fn(game)
            else:
                print("Unknown command. Use " + "/".join(COMMANDS.keys()))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        GPIO.cleanup()
        print("\nGPIO cleaned up. Done.")
