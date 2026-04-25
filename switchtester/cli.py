"""
Interactive CLI for the switch matrix tester.

All user-facing commands live here. Hardware logic is in tester.py.
"""

import sys
import time

from .tester import (
    COL_PINS,
    GPIO,
    GPIO_LIBRARY,
    ROW_PINS,
    diode_scan,
    load_game,
    detect_stuck_low_pins,
    pin_continuity_scan,
    pin_label,
    read_switch,
    remap_return,
    remap_strobe,
    save_platform,
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


def _remap_one(idx, kind, game):
    """Scan once and remap if the detected BCM doesn't match expected. Returns True if remapped."""
    expected_bcm = COL_PINS[idx] if kind == "strobe" else ROW_PINS[idx]
    label = pin_label(expected_bcm)

    while True:
        print(f"\nTesting {label}:")
        cmd = input("  Connect jumper, then press Enter (s=skip, q=quit): ").strip().lower()
        if cmd == "q":
            return None  # signal quit
        if cmd == "s":
            return False

        pairs = pin_continuity_scan()
        setup_gpio(game)

        if not pairs:
            choice = input("  No connection detected. Press Enter to retry, s=skip, q=quit: ").strip().lower()
            if choice == "q":
                return None
            if choice == "s":
                return False
            continue

        if len(pairs) > 1:
            print(f"  Multiple pairs detected -- remove extra jumpers and retry.")
            for p in pairs:
                a, b = sorted(p)
                print(f"    {pin_label(a)} <-> {pin_label(b)}")
            return False

        pair = next(iter(pairs))
        a, b = sorted(pair)

        if expected_bcm in pair:
            other = b if expected_bcm == a else a
            print(f"  CONFIRMED: {label} <-> {pin_label(other)}")
            return False

        # Mismatch
        print(f"  MISMATCH: expected {label}, but detected:")
        print(f"    {pin_label(a)} <-> {pin_label(b)}")

        # Offer the two detected BCMs as remap candidates, plus retest
        candidates = [x for x in [a, b] if x != expected_bcm]
        print(f"  Which pin should be {label}?")
        for i, c in enumerate(candidates):
            print(f"    {i+1}) {pin_label(c)}")
        print(f"    t) retest")
        print(f"    0) No change")
        choice = input("  Choice: ").strip().lower()
        if choice == "t":
            continue
        if choice in ("1", "2"):
            new_bcm = candidates[int(choice) - 1]
            swapped_label = pin_label(new_bcm)
            if kind == "strobe":
                remap_strobe(idx, new_bcm)
            else:
                remap_return(idx, new_bcm)
            print(f"  Remapped: {label} swapped with {swapped_label}.")
            return True
        return False


def cmd_remap_pins(game):
    """Guided step-by-step pin verification and remapping."""
    print("\n--- Guided pin mapper ---")
    print("For each pin, connect a jumper from that pin to any other GPIO pin.")
    print("The scanner detects both endpoints and verifies the expected BCM.\n")

    pins = (
        [(i, "strobe") for i in range(len(COL_PINS))] +
        [(i, "return") for i in range(len(ROW_PINS))]
    )

    changed = False
    for idx, kind in pins:
        result = _remap_one(idx, kind, game)
        if result is None:
            break
        if result:
            changed = True

    print()
    if changed:
        ans = input(f"Save updated pin map to {game['platform_path']}? [y/N]: ").strip().lower()
        if ans == "y":
            save_platform(game["platform_path"])
            print(f"Saved {game['platform_path']}\n")
    else:
        print("No changes made.\n")


def cmd_pin_continuity(game):
    """Continuous monitor showing which GPIO pins are directly connected."""
    print("\n--- Pin continuity tester ---")
    print("Connect a jumper between any two header pins.")
    print("Ctrl+C to stop.\n")

    stuck = detect_stuck_low_pins()
    if stuck:
        for p in stuck:
            print(f"WARNING: {pin_label(p)} (BCM {p}) is stuck LOW -- excluded from scan")
        print("  (Hardware pull-up not working on this pin; likely a GPIO controller quirk.)")
        print()

    prev = set()
    try:
        while True:
            current = pin_continuity_scan(skip=stuck)

            for pair in current - prev:
                a, b = sorted(pair)
                print(f"CONNECTED: {pin_label(a)} <-> {pin_label(b)}")

            for pair in prev - current:
                a, b = sorted(pair)
                print(f"REMOVED:   {pin_label(a)} <-> {pin_label(b)}")

            prev = current
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped\n")
    finally:
        setup_gpio(game)


COMMANDS = {
    "m": ("monitor mode (continuous scan)", cmd_monitor),
    "d": ("diode reverse bias test", cmd_diode_test),
    "w": ("walk test (guided switch-by-switch)", cmd_walk_test),
    "s": ("snapshot matrix state", cmd_snapshot),
    "l": ("list all switches with wire colours", cmd_list_switches),
    "p": ("pin continuity tester (jumper two pins to identify them)", cmd_pin_continuity),
    "r": ("remap pins (guided verify and remap GPIO assignments)", cmd_remap_pins),
    "h": ("show this help", None),
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
    print(f"GPIO:   {GPIO_LIBRARY}")
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
            elif cmd == "h":
                print()
                for key, (description, _) in COMMANDS.items():
                    print(f"  {key} = {description}")
                print()
            else:
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
