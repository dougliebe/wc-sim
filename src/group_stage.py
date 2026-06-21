from itertools import combinations
import numpy as np
from src.match import simulate_group_matches_vectorized


_PAIR_INDICES = list(combinations(range(4), 2))  # (0,1),(0,2),(0,3),(1,2),(1,3),(2,3)


def simulate_all_groups(
    groups: dict[str, list[str]],
    elos: dict[str, float],
    rng: np.random.Generator,
    known_results: dict[tuple[str, str], tuple[int, int]] | None = None,
) -> dict[str, list[dict]]:
    """
    Simulate all groups in one vectorised batch.
    known_results: scorelines already played, keyed by (team_a, team_b) in either order.
    Returns {group_letter: ranked_team_list}.
    """
    if known_results is None:
        known_results = {}

    # Collect unknown matches for vectorised simulation
    all_pairs: list[tuple[str, str]] = []
    group_meta: dict[str, tuple[list[tuple[str, str]], list[int | None]]] = {}

    for letter, teams in groups.items():
        pairs_for_group = [(teams[i], teams[j]) for i, j in _PAIR_INDICES]
        sim_indices: list[int | None] = []
        for pair in pairs_for_group:
            a, b = pair
            if (a, b) in known_results or (b, a) in known_results:
                sim_indices.append(None)  # will use known result
            else:
                sim_indices.append(len(all_pairs))
                all_pairs.append(pair)
        group_meta[letter] = (pairs_for_group, sim_indices)

    # Single vectorised call for all unknown matches
    sim_scorelines = simulate_group_matches_vectorized(all_pairs, elos, rng) if all_pairs else []

    results = {}
    for letter, teams in groups.items():
        pairs_for_group, sim_indices = group_meta[letter]
        scorelines: list[tuple[int, int]] = []
        for pair, idx in zip(pairs_for_group, sim_indices):
            if idx is None:
                a, b = pair
                if (a, b) in known_results:
                    scorelines.append(known_results[(a, b)])
                else:
                    ga, gb = known_results[(b, a)]
                    scorelines.append((gb, ga))
            else:
                scorelines.append(sim_scorelines[idx])
        results[letter] = _tally_and_rank(teams, pairs_for_group, scorelines)

    return results


def _tally_and_rank(
    teams: list[str],
    pairs: list[tuple[str, str]],
    scorelines: list[tuple[int, int]],
) -> list[dict]:
    stats   = {t: {"team": t, "pts": 0, "gf": 0, "ga": 0, "gd": 0} for t in teams}
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

    return _rank_group(list(stats.values()), results)


# Keep single-group entry point for compatibility / testing
def simulate_group(teams: list[str], elos: dict[str, float], rng: np.random.Generator) -> list[dict]:
    pairs = [(teams[i], teams[j]) for i, j in _PAIR_INDICES]
    scorelines = simulate_group_matches_vectorized(pairs, elos, rng)
    return _tally_and_rank(teams, pairs, scorelines)


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
        if ga is None:
            continue
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


def _get_result(a: str, b: str, results: dict) -> tuple[int, int] | tuple[None, None]:
    if (a, b) in results:
        return results[(a, b)]
    if (b, a) in results:
        gb, ga = results[(b, a)]
        return ga, gb
    return None, None
