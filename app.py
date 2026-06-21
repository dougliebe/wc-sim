"""
Flask app for the 2026 World Cup group stage visualizer.
Run: flask run  (or python app.py)
"""
import json
from flask import Flask, jsonify, render_template, request

from data.elos import ELOS
from data.results import RESULTS
from src.groups import GROUPS
from src.viz import (
    current_standings,
    group_matches,
    group_position_probs,
    resolve_with_scores,
)

app = Flask(__name__)

# ── cache overview probs on startup ──────────────────────────────────────────
_overview_cache: dict = {}

def _build_overview_cache():
    global _overview_cache
    cache = {}
    for letter in GROUPS:
        probs = group_position_probs(letter, RESULTS, ELOS, n=20_000)
        standings = current_standings(letter, RESULTS)
        matches = group_matches(letter, RESULTS)
        cache[letter] = {"probs": probs, "standings": standings, "matches": matches}
    _overview_cache = cache

with app.app_context():
    _build_overview_cache()


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/overview")
def api_overview():
    return jsonify(_overview_cache)


@app.route("/api/group/<letter>")
def api_group(letter: str):
    letter = letter.upper()
    if letter not in GROUPS:
        return jsonify({"error": "unknown group"}), 404
    matches = group_matches(letter, RESULTS)
    standings = current_standings(letter, RESULTS)
    probs = _overview_cache[letter]["probs"]
    ranked, reasons = resolve_with_scores(letter, RESULTS)
    return jsonify({
        "letter": letter,
        "matches": matches,
        "standings": standings,
        "probs": probs,
        "ranked": ranked,
        "tiebreak_reasons": reasons,
    })


@app.route("/api/group/<letter>/simulate", methods=["POST"])
def api_simulate(letter: str):
    letter = letter.upper()
    if letter not in GROUPS:
        return jsonify({"error": "unknown group"}), 404

    body = request.get_json(force=True)
    # scores: list of {home, away, home_score, away_score}
    # Merge with RESULTS: user scores override known results for unplayed matches
    known = dict(RESULTS)
    for m in body.get("scores", []):
        if m["home_score"] is not None and m["away_score"] is not None:
            known[(m["home"], m["away"])] = (int(m["home_score"]), int(m["away_score"]))

    # Filter to only this group's teams
    group_teams = set(GROUPS[letter])
    group_known = {k: v for k, v in known.items() if k[0] in group_teams and k[1] in group_teams}

    probs = group_position_probs(letter, group_known, ELOS, n=20_000)
    ranked, reasons = resolve_with_scores(letter, group_known)
    standings = current_standings(letter, group_known)

    return jsonify({
        "probs": probs,
        "ranked": ranked,
        "tiebreak_reasons": reasons,
        "standings": standings,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
