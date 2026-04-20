"""
Flask web interface for the switch matrix tester.

Provides game selection and four test modes (list, snapshot, diode, monitor)
as simple mobile-friendly pages. Walk test, pin continuity, and remap are
CLI-only -- they require interactive back-and-forth that doesn't suit a page.
"""

import glob
import json
import os
import threading
import time

from flask import Flask, Response, render_template, stream_with_context, url_for

from .tester import diode_scan, load_game, scan_matrix, setup_gpio

app = Flask(__name__)

_game = None
_game_slug = None
_gpio_lock = threading.Lock()
_games_dir = "games"


def _games_list():
    result = []
    for path in sorted(glob.glob(os.path.join(_games_dir, "*.json"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        try:
            with open(path) as f:
                data = json.load(f)
            name = data.get("game", slug)
        except (OSError, json.JSONDecodeError):
            name = slug
        result.append((slug, name))
    return result


def _load_game_if_needed(slug):
    global _game, _game_slug
    if _game_slug != slug:
        path = os.path.join(_games_dir, f"{slug}.json")
        _game = load_game(path)
        setup_gpio(_game)
        _game_slug = slug
    return _game


@app.route("/")
def index():
    return render_template("index.html", games=_games_list())


@app.route("/game/<slug>")
def game_dashboard(slug):
    with _gpio_lock:
        game = _load_game_if_needed(slug)
    return render_template("game.html", game=game, slug=slug)


@app.route("/game/<slug>/list")
def switch_list(slug):
    with _gpio_lock:
        game = _load_game_if_needed(slug)
    switches = sorted(
        [
            {
                "num": sw_num,
                "name": name,
                "strobe": game["strobe_wires"].get(col, "?"),
                "ret": game["return_wires"].get(row, "?"),
            }
            for (col, row), (sw_num, name) in game["switch_map"].items()
        ],
        key=lambda s: s["num"],
    )
    return render_template("list.html", game=game, slug=slug, switches=switches)


@app.route("/game/<slug>/snapshot")
def snapshot(slug):
    with _gpio_lock:
        game = _load_game_if_needed(slug)
        closed = scan_matrix(game)
    grid = []
    for r in range(game["num_rows"]):
        row_cells = []
        for c in range(game["num_cols"]):
            sw_num, name = game["switch_map"].get((c, r), (0, "?"))
            row_cells.append({"num": sw_num, "name": name, "closed": (c, r) in closed})
        grid.append(row_cells)
    return render_template("snapshot.html", game=game, slug=slug, grid=grid)


@app.route("/game/<slug>/diode")
def diode(slug):
    with _gpio_lock:
        game = _load_game_if_needed(slug)
        shorted = diode_scan(game)
    results = []
    for col, row in shorted:
        sw_num, name = game["switch_map"].get((col, row), (0, "?"))
        results.append({
            "num": sw_num,
            "name": name,
            "strobe": game["strobe_wires"].get(col, "?"),
            "ret": game["return_wires"].get(row, "?"),
        })
    return render_template("diode.html", game=game, slug=slug, results=results)


@app.route("/game/<slug>/monitor")
def monitor(slug):
    with _gpio_lock:
        game = _load_game_if_needed(slug)
    stream_url = url_for("monitor_stream", slug=slug)
    return render_template("monitor.html", game=game, slug=slug, stream_url=stream_url)


@app.route("/game/<slug>/monitor/stream")
def monitor_stream(slug):
    def generate():
        prev = set()
        while True:
            with _gpio_lock:
                current = scan_matrix(_game)
            for pos in current - prev:
                col, row = pos
                sw_num, name = _game["switch_map"].get(pos, (0, "?"))
                yield "data: " + json.dumps({
                    "event": "closed", "num": sw_num, "name": name,
                    "col": col, "row": row,
                }) + "\n\n"
            for pos in prev - current:
                col, row = pos
                sw_num, name = _game["switch_map"].get(pos, (0, "?"))
                yield "data: " + json.dumps({
                    "event": "opened", "num": sw_num, "name": name,
                    "col": col, "row": row,
                }) + "\n\n"
            prev = current
            time.sleep(0.02)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def main():
    global _games_dir
    import argparse

    parser = argparse.ArgumentParser(description="Switch tester web interface")
    parser.add_argument(
        "--games-dir", default="games",
        help="Directory containing game JSON files (default: games)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    _games_dir = args.games_dir
    print(f"Switch tester web UI -- http://0.0.0.0:{args.port}")
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
