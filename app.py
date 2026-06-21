"""
Flask app for the 2026 World Cup group stage visualizer.
Run: flask run  (or python app.py)
"""
from flask import Flask, jsonify, render_template, request

from data.elos import ELOS
from data.results import RESULTS
from src.groups import GROUPS
from src.bracket import R32_SLOT_OPPONENTS
from src.viz import (
    all_groups_advancement_probs,
    current_standings,
    group_matches,
    resolve_with_scores,
)

app = Flask(__name__)

# ── cache on startup (all 12 groups, 20k sims, ~3-5s) ────────────────────────
_adv_cache: dict = {}   # team -> {pos, advance, third_advance, r32_slots}
_overview_cache: dict = {}  # letter -> {standings, matches, adv_data_by_team}

def _build_cache():
    global _adv_cache, _overview_cache
    _adv_cache = all_groups_advancement_probs(RESULTS, ELOS, n=20_000)
    cache = {}
    for letter in GROUPS:
        standings = current_standings(letter, RESULTS)
        matches = group_matches(letter, RESULTS)
        teams = GROUPS[letter]
        cache[letter] = {
            "standings": standings,
            "matches": matches,
            "adv": {t: _adv_cache[t] for t in teams},
        }
    _overview_cache = cache

with app.app_context():
    _build_cache()


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
    ranked, reasons = resolve_with_scores(letter, RESULTS)
    teams = GROUPS[letter]
    adv = {t: _adv_cache[t] for t in teams}
    return jsonify({
        "letter": letter,
        "matches": matches,
        "standings": standings,
        "adv": adv,
        "ranked": ranked,
        "tiebreak_reasons": reasons,
        "slot_opponents": R32_SLOT_OPPONENTS,
    })


@app.route("/api/group/<letter>/simulate", methods=["POST"])
def api_simulate(letter: str):
    letter = letter.upper()
    if letter not in GROUPS:
        return jsonify({"error": "unknown group"}), 404

    body = request.get_json(force=True)
    # Merge user-supplied hypothetical scores for this group into global RESULTS
    known = dict(RESULTS)
    for m in body.get("scores", []):
        if m["home_score"] is not None and m["away_score"] is not None:
            known[(m["home"], m["away"])] = (int(m["home_score"]), int(m["away_score"]))

    # Filter to this group only for deterministic standings/tiebreakers
    group_teams = set(GROUPS[letter])
    group_known = {k: v for k, v in known.items() if k[0] in group_teams and k[1] in group_teams}

    # Run all-groups sim with hypothetical scores merged in (other groups use RESULTS)
    adv_all = all_groups_advancement_probs(known, ELOS, n=20_000)
    adv = {t: adv_all[t] for t in GROUPS[letter]}

    ranked, reasons = resolve_with_scores(letter, group_known)
    standings = current_standings(letter, group_known)

    return jsonify({
        "adv": adv,
        "ranked": ranked,
        "tiebreak_reasons": reasons,
        "standings": standings,
        "slot_opponents": R32_SLOT_OPPONENTS,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
