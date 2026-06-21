import numpy as np
from src.groups import GROUPS
from src.group_stage import simulate_group
from src.third_place import select_third_place
from src.bracket import assign_third_place, build_r32_matchups, R16_PAIRS, QF_PAIRS, SF_PAIRS
from src.match import simulate_knockout


def simulate_once(elos: dict[str, float], rng: np.random.Generator) -> dict[str, int]:
    """
    Run one full tournament simulation.
    Returns dict: team -> round reached
        0 = group stage exit
        1 = Round of 32 exit
        2 = Round of 16 exit
        3 = Quarterfinal exit
        4 = Semifinal exit
        5 = Final (runner-up)
        6 = Champion
    """
    reached = {team: 0 for group in GROUPS.values() for team in group}

    # --- Group stage ---
    group_finishers = {}   # group_letter -> {1: team, 2: team, 3: team, 4: team}
    third_place_teams = []

    for letter, teams in GROUPS.items():
        ranked = simulate_group(teams, elos, rng)
        group_finishers[letter] = {i + 1: ranked[i]["team"] for i in range(4)}
        third_entry = ranked[2].copy()
        third_entry["group_letter"] = letter
        third_place_teams.append(third_entry)

    # --- Third-place selection ---
    advancing_8, _ = select_third_place(third_place_teams)
    advancing_set = {t["team"] for t in advancing_8}

    # Mark Round of 32 qualifiers (positions 1 and 2 from each group + advancing 3rds)
    for letter, finishers in group_finishers.items():
        reached[finishers[1]] = 1
        reached[finishers[2]] = 1
        if finishers[3] in advancing_set:
            reached[finishers[3]] = 1
        # 4th place stays at 0 (group exit)

    # --- Build R32 bracket ---
    third_assignments = assign_third_place(advancing_8, group_finishers)
    r32_matchups = build_r32_matchups(group_finishers, third_assignments)

    # --- Simulate knockout rounds ---
    r32_winners = _simulate_round(r32_matchups, elos, rng, reached, exit_round=1, advance_round=2)
    r16_matchups = _pair_winners(r32_winners, R16_PAIRS)
    r16_winners = _simulate_round(r16_matchups, elos, rng, reached, exit_round=2, advance_round=3)
    qf_matchups = _pair_winners(r16_winners, QF_PAIRS)
    qf_winners = _simulate_round(qf_matchups, elos, rng, reached, exit_round=3, advance_round=4)
    sf_matchups = _pair_winners(qf_winners, SF_PAIRS)
    sf_winners = _simulate_round(sf_matchups, elos, rng, reached, exit_round=4, advance_round=5)

    # Final
    finalists = sf_winners
    winner = _knockout_match(finalists[0], finalists[1], elos, rng)
    loser = finalists[1] if winner == finalists[0] else finalists[0]
    reached[loser] = 5
    reached[winner] = 6

    return reached


def _simulate_round(
    matchups: list[tuple[str, str]],
    elos: dict,
    rng: np.random.Generator,
    reached: dict,
    exit_round: int,
    advance_round: int,
) -> list[str]:
    winners = []
    for a, b in matchups:
        w = _knockout_match(a, b, elos, rng)
        loser = b if w == a else a
        reached[loser] = exit_round
        reached[w] = advance_round
        winners.append(w)
    return winners


def _knockout_match(a: str, b: str, elos: dict, rng: np.random.Generator) -> str:
    result = simulate_knockout(elos[a], elos[b], rng)
    return a if result == "A" else b


def _pair_winners(winners: list[str], pairs: list[tuple[int, int]]) -> list[tuple[str, str]]:
    return [(winners[i], winners[j]) for i, j in pairs]
