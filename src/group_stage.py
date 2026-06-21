from itertools import combinations
import numpy as np
from src.match import simulate_group_matches_vectorized


# Pre-compute match order for a 4-team group (indices into team list)
_PAIR_INDICES = list(combinations(range(4), 2))


def simulate_group(teams: list[str], elos: dict[str, float], rng: np.random.Generator) -> list[dict]:
    """
    Simulate a round-robin group of 4 teams.
    Returns list of team stat dicts sorted 1st to 4th.
    """
    pairs = [(teams[i], teams[j]) for i, j in _PAIR_INDICES]
    scorelines = simulate_group_matches_vectorized(pairs, elos, rng)

    stats = {t: {"team": t, "pts": 0, "gf": 0, "ga": 0, "gd": 0} for t in teams}
    results = {}

    for (a, b), (ga, gb) in zip(pairs, scorelines):
        results[(a, b)] = (ga, gb)
        stats[a]["gf"] += ga
        stats[a]["ga"] += gb
        stats[b]["gf"] += gb
        stats[b]["ga"] += ga
        if ga > gb:
            stats[a]["pts"] += 3
        elif ga == gb:
            stats[a]["pts"] += 1
            stats[b]["pts"] += 1
        else:
            stats[b]["pts"] += 3

    for t in teams:
        stats[t]["gd"] = stats[t]["gf"] - stats[t]["ga"]

    ranked = _rank_group(list(stats.values()), results)
    return ranked


def _rank_group(team_stats: list[dict], results: dict) -> list[dict]:
    by_pts = sorted(team_stats, key=lambda s: s["pts"], reverse=True)
    return _resolve_ties(by_pts, results)


def _resolve_ties(sorted_stats: list[dict], results: dict) -> list[dict]:
    final = []
    i = 0
    while i < len(sorted_stats):
        j = i + 1
        while j < len(sorted_stats) and sorted_stats[j]["pts"] == sorted_stats[i]["pts"]:
            j += 1
        tied = sorted_stats[i:j]
        if len(tied) == 1:
            final.append(tied[0])
        else:
            final.extend(_break_tie(tied, results))
        i = j
    return final


def _break_tie(tied: list[dict], results: dict) -> list[dict]:
    teams = [s["team"] for s in tied]
    stats_by_team = {s["team"]: s for s in tied}

    h2h = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
    for a, b in combinations(teams, 2):
        ga, gb = _get_result(a, b, results)
        h2h[a]["gf"] += ga
        h2h[a]["gd"] += ga - gb
        h2h[b]["gf"] += gb
        h2h[b]["gd"] += gb - ga
        if ga > gb:
            h2h[a]["pts"] += 3
        elif ga == gb:
            h2h[a]["pts"] += 1
            h2h[b]["pts"] += 1
        else:
            h2h[b]["pts"] += 3

    def sort_key(t):
        s = stats_by_team[t]
        return (
            h2h[t]["pts"],
            h2h[t]["gd"],
            h2h[t]["gf"],
            s["gd"],
            s["gf"],
        )

    sorted_teams = sorted(teams, key=sort_key, reverse=True)

    result = []
    i = 0
    while i < len(sorted_teams):
        j = i + 1
        while j < len(sorted_teams) and sort_key(sorted_teams[j]) == sort_key(sorted_teams[i]):
            j += 1
        sub = sorted_teams[i:j]
        if len(sub) > 1:
            import random
            random.shuffle(sub)
        result.extend([stats_by_team[t] for t in sub])
        i = j
    return result


def _get_result(a: str, b: str, results: dict) -> tuple[int, int]:
    if (a, b) in results:
        return results[(a, b)]
    ga, gb = results[(b, a)]
    return gb, ga
