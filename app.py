"""
Flask app for the 2026 World Cup group stage visualizer.
Run: flask run  (or python app.py)
"""
from flask import Flask, jsonify, render_template, request

from data.elos import ELOS
from data.results import RESULTS
from src.groups import GROUPS
from src.bracket import R32_SLOT_OPPONENTS, R32_SLOT_GROUPS
from src.viz import (
    all_groups_advancement_probs,
    recompute_group_advancement,
    current_standings,
    group_matches,
    resolve_with_scores,
)

app = Flask(__name__)

# ── cache on startup (all 12 groups, 20k sims, ~3-5s) ────────────────────────
_adv_cache: dict = {}        # team -> {pos, advance, third_advance, r32_slots}
_overview_cache: dict = {}   # letter -> {standings, matches, adv}
_third_entry_cache: list = []  # n lists of 12 third-place dicts (for fast simulate)

def _build_cache():
    global _adv_cache, _overview_cache, _third_entry_cache
    _adv_cache, _third_entry_cache = all_groups_advancement_probs(RESULTS, ELOS, n=20_000)
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
        "slot_groups": R32_SLOT_GROUPS,
    })


@app.route("/api/group/<letter>/simulate", methods=["POST"])
def api_simulate(letter: str):
    letter = letter.upper()
    if letter not in GROUPS:
        return jsonify({"error": "unknown group"}), 404

    body = request.get_json(force=True)
    # Merge user-supplied hypothetical scores for this group into actual results
    known = dict(RESULTS)
    for m in body.get("scores", []):
        if m["home_score"] is not None and m["away_score"] is not None:
            known[(m["home"], m["away"])] = (int(m["home_score"]), int(m["away_score"]))

    # Filter to this group only for deterministic standings/tiebreakers
    group_teams = set(GROUPS[letter])
    group_known = {k: v for k, v in known.items() if k[0] in group_teams and k[1] in group_teams}

    # Resimulate only this group; cross-join with cached 3rd-place entries from
    # the other 11 groups to compute advancement probs correctly without a full re-run.
    # Returns updated adv for all 48 teams (other groups' pos probs are unchanged but
    # their 3rd-place advancement probs shift because the pool composition changed).
    adv_all = recompute_group_advancement(
        letter, group_known, ELOS, _third_entry_cache, _adv_cache, n=20_000
    )

    ranked, reasons = resolve_with_scores(letter, group_known)
    standings = current_standings(letter, group_known)

    # Build per-group adv snapshot for the overview cards
    group_adv_overview = {}
    for grp, grp_teams in GROUPS.items():
        group_adv_overview[grp] = {t: adv_all[t] for t in grp_teams}

    return jsonify({
        "adv": adv_all,
        "group_adv_overview": group_adv_overview,
        "ranked": ranked,
        "tiebreak_reasons": reasons,
        "standings": standings,
        "slot_opponents": R32_SLOT_OPPONENTS,
        "slot_groups": R32_SLOT_GROUPS,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
