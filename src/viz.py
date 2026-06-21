"""
Helpers for the group stage visualizer (app.py).
"""
from itertools import combinations
import numpy as np

import numpy as np_top  # alias to avoid shadowing
from src.groups import GROUPS
from src.group_stage import (
    _tally_and_rank,
    _PAIR_INDICES,
    simulate_group_matches_vectorized,
    simulate_all_groups,
)
from src.third_place import select_third_place
from src.bracket import assign_third_place, R32_SLOT_OPPONENTS


def current_standings(letter: str, known_results: dict) -> list[dict]:
    """
    Return partial standings for a group based only on played matches.
    Unplayed matches contribute nothing. Each entry has:
      team, pts, gf, ga, gd, played
    Ordered by: pts desc, gd desc, gf desc (no tiebreaker, not final).
    """
    teams = GROUPS[letter]
    stats = {t: {"team": t, "pts": 0, "gf": 0, "ga": 0, "gd": 0, "played": 0} for t in teams}

    for i, j in _PAIR_INDICES:
        a, b = teams[i], teams[j]
        ga, gb = None, None
        if (a, b) in known_results:
            ga, gb = known_results[(a, b)]
        elif (b, a) in known_results:
            gb, ga = known_results[(b, a)]
        if ga is None:
            continue
        stats[a]["gf"] += ga; stats[a]["ga"] += gb; stats[a]["played"] += 1
        stats[b]["gf"] += gb; stats[b]["ga"] += ga; stats[b]["played"] += 1
        if ga > gb:
            stats[a]["pts"] += 3
        elif ga == gb:
            stats[a]["pts"] += 1; stats[b]["pts"] += 1
        else:
            stats[b]["pts"] += 3

    for t in teams:
        stats[t]["gd"] = stats[t]["gf"] - stats[t]["ga"]

    return sorted(stats.values(), key=lambda s: (s["pts"], s["gd"], s["gf"]), reverse=True)


def resolve_with_scores(letter: str, all_scores: dict) -> tuple[list[dict], dict[str, str]]:
    """
    Given a complete (or partial) set of scorelines for a group, return:
      - ranked list of team stat dicts (same structure as _tally_and_rank)
      - tiebreak_reasons: {team: reason_string} for teams resolved via tiebreaker
        e.g. {"Mexico": "H2H pts", "Korea Republic": "H2H GD", ...}
    """
    teams = GROUPS[letter]
    pairs = [(teams[i], teams[j]) for i, j in _PAIR_INDICES]

    # Build scorelines list; skip pairs not in all_scores
    scorelines = []
    valid_pairs = []
    for a, b in pairs:
        if (a, b) in all_scores:
            scorelines.append(all_scores[(a, b)])
            valid_pairs.append((a, b))
        elif (b, a) in all_scores:
            gb, ga = all_scores[(b, a)]
            scorelines.append((gb, ga))
            valid_pairs.append((a, b))

    ranked = _tally_and_rank(teams, valid_pairs, scorelines)
    reasons = _tiebreak_reasons(teams, ranked, all_scores)
    return ranked, reasons


def _tiebreak_reasons(teams: list[str], ranked: list[dict], results: dict) -> dict[str, str]:
    """
    For each team in ranked, determine if and how it was separated from the team above it.
    Returns {team: reason} where reason is one of:
      "pts" | "H2H pts" | "H2H GD" | "H2H GF" | "Overall GD" | "Overall GF" | "Random draw" | ""
    """
    reasons: dict[str, str] = {t["team"]: "" for t in ranked}

    i = 0
    while i < len(ranked):
        # Find the extent of the pts-tied block
        j = i + 1
        while j < len(ranked) and ranked[j]["pts"] == ranked[i]["pts"]:
            j += 1
        tied_block = ranked[i:j]
        if len(tied_block) > 1:
            tied_teams = [s["team"] for s in tied_block]
            _annotate_tiebreak(tied_teams, tied_block, results, reasons)
        i = j
    return reasons


def _annotate_tiebreak(tied_teams, tied_block, results, reasons):
    stats_by_team = {s["team"]: s for s in tied_block}

    h2h = {t: {"pts": 0, "gd": 0, "gf": 0} for t in tied_teams}
    for a, b in combinations(tied_teams, 2):
        ga, gb = _get_h2h(a, b, results)
        if ga is None:
            continue
        h2h[a]["gf"] += ga; h2h[a]["gd"] += ga - gb
        h2h[b]["gf"] += gb; h2h[b]["gd"] += gb - ga
        if ga > gb:
            h2h[a]["pts"] += 3
        elif ga == gb:
            h2h[a]["pts"] += 1; h2h[b]["pts"] += 1
        else:
            h2h[b]["pts"] += 3

    def key(t):
        s = stats_by_team[t]
        return (h2h[t]["pts"], h2h[t]["gd"], h2h[t]["gf"], s["gd"], s["gf"])

    criteria_labels = ["H2H pts", "H2H GD", "H2H GF", "Overall GD", "Overall GF"]

    for idx, t in enumerate(tied_teams):
        if idx == 0:
            continue  # first in group, no separator needed
        above = tied_teams[idx - 1]
        k_t = key(t)
        k_a = key(above)
        reason = "Random draw"
        for c_idx, (v_above, v_t) in enumerate(zip(k_a, k_t)):
            if v_above != v_t:
                reason = criteria_labels[c_idx]
                break
        reasons[t] = reason


def _get_h2h(a, b, results):
    if (a, b) in results:
        return results[(a, b)]
    if (b, a) in results:
        gb, ga = results[(b, a)]
        return ga, gb
    return None, None


def group_position_probs(
    letter: str,
    known_results: dict,
    elos: dict,
    n: int = 20_000,
) -> dict[str, dict[str, float]]:
    """
    Monte Carlo position probabilities for a single group.
    Returns {team: {"1st": p, "2nd": p, "3rd": p, "4th": p}}.
    """
    teams = GROUPS[letter]
    pairs = [(teams[i], teams[j]) for i, j in _PAIR_INDICES]

    # Separate known vs unknown pairs
    unknown_pairs = []
    for a, b in pairs:
        if (a, b) not in known_results and (b, a) not in known_results:
            unknown_pairs.append((a, b))

    counts = {t: [0, 0, 0, 0] for t in teams}  # index 0=1st, 1=2nd, 2=3rd, 3=4th

    if not unknown_pairs:
        # All matches known — deterministic
        ranked, _ = resolve_with_scores(letter, known_results)
        for pos, entry in enumerate(ranked):
            counts[entry["team"]][pos] = n
    else:
        rng = np.random.default_rng()
        # Vectorize: simulate all unknown pairs for all n sims at once
        # Shape: (n * len(unknown_pairs),) flattened then reshaped
        nu = len(unknown_pairs)
        all_pairs_batch = unknown_pairs * n
        all_scores_sim = simulate_group_matches_vectorized(all_pairs_batch, elos, rng)

        # Build known part once
        known_scores = {}
        for a, b in pairs:
            if (a, b) in known_results:
                known_scores[(a, b)] = known_results[(a, b)]
            elif (b, a) in known_results:
                gb, ga = known_results[(b, a)]
                known_scores[(a, b)] = (ga, gb)

        for sim_i in range(n):
            sim_scores = dict(known_scores)
            for pair_i, (a, b) in enumerate(unknown_pairs):
                sim_scores[(a, b)] = all_scores_sim[sim_i * nu + pair_i]
            ranked = _tally_and_rank(teams, pairs, [sim_scores.get((a, b), sim_scores.get((b, a), (0, 0))) for a, b in pairs])
            for pos, entry in enumerate(ranked):
                counts[entry["team"]][pos] += 1

    return {
        t: {"1st": counts[t][0] / n, "2nd": counts[t][1] / n,
            "3rd": counts[t][2] / n, "4th": counts[t][3] / n}
        for t in teams
    }


def all_groups_advancement_probs(
    known_results: dict,
    elos: dict,
    n: int = 20_000,
) -> dict[str, dict]:
    """
    Run N full group-stage simulations (all 12 groups simultaneously) and compute:
      - P(finish 1st/2nd/3rd/4th) within group
      - P(advance to R32) = P(1st) + P(2nd) + P(3rd AND qualifies as top-8 third-place)
      - P(advance | finish 3rd)
      - R32 slot distribution for 3rd-place teams (which opponent they'd face)

    Returns {team: {pos, advance, third_advance, r32_slots}} for all 48 teams.
    r32_slots: {slot_id_str: fraction} — only meaningful for teams that can finish 3rd.
    """
    rng = np.random.default_rng()
    all_teams = [t for teams in GROUPS.values() for t in teams]

    pos_counts = {t: [0, 0, 0, 0] for t in all_teams}       # [1st,2nd,3rd,4th]
    advance_counts = {t: 0 for t in all_teams}
    third_counts = {t: 0 for t in all_teams}                 # sims where team finished 3rd
    slot_counts = {t: {} for t in all_teams}                 # {slot_id: count}

    for _ in range(n):
        group_results = simulate_all_groups(GROUPS, elos, rng, known_results)

        third_place_entries = []
        group_finishers = {}

        for letter, ranked in group_results.items():
            group_finishers[letter] = {i + 1: ranked[i]["team"] for i in range(4)}
            for pos, entry in enumerate(ranked):
                pos_counts[entry["team"]][pos] += 1
                if pos < 2:  # 1st or 2nd always advance
                    advance_counts[entry["team"]] += 1
            # Collect 3rd-place entry for cross-group ranking
            third_entry = ranked[2].copy()
            third_entry["group_letter"] = letter
            third_place_entries.append(third_entry)
            third_counts[ranked[2]["team"]] += 1

        advancing_8, _ = select_third_place(third_place_entries)
        advancing_set = {t["team"] for t in advancing_8}

        for team in advancing_set:
            advance_counts[team] += 1

        # Annex C slot assignment for advancing 3rd-place teams
        try:
            third_assignments = assign_third_place(advancing_8, group_finishers)
            for slot_id, team in third_assignments.items():
                slot_counts[team][slot_id] = slot_counts[team].get(slot_id, 0) + 1
        except Exception:
            pass  # rare edge case in assignment; skip slot tracking for this sim

    result = {}
    for team in all_teams:
        tc = third_counts[team]
        adv = advance_counts[team]
        result[team] = {
            "pos": {
                "1st": pos_counts[team][0] / n,
                "2nd": pos_counts[team][1] / n,
                "3rd": pos_counts[team][2] / n,
                "4th": pos_counts[team][3] / n,
            },
            "advance": adv / n,
            "third_advance": (adv - pos_counts[team][0] - pos_counts[team][1]) / tc if tc > 0 else 0.0,
            "r32_slots": {
                str(sid): cnt / n
                for sid, cnt in slot_counts[team].items()
            },
        }
    return result


def group_matches(letter: str, known_results: dict) -> list[dict]:
    """
    Return all 6 matches for a group with played scores and played flag.
    """
    teams = GROUPS[letter]
    matches = []
    for i, j in _PAIR_INDICES:
        a, b = teams[i], teams[j]
        if (a, b) in known_results:
            ga, gb = known_results[(a, b)]
            matches.append({"home": a, "away": b, "home_score": ga, "away_score": gb, "played": True})
        elif (b, a) in known_results:
            gb, ga = known_results[(b, a)]
            matches.append({"home": a, "away": b, "home_score": ga, "away_score": gb, "played": True})
        else:
            matches.append({"home": a, "away": b, "home_score": None, "away_score": None, "played": False})
    return matches
