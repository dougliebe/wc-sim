import numpy as np
from src.groups import GROUPS
from src.group_stage import simulate_all_groups
from src.third_place import select_third_place
from src.bracket import assign_third_place, build_r32_matchups, R16_PAIRS, QF_PAIRS, SF_PAIRS
from src.match import simulate_knockout, build_ko_table


def build_tables(elos: dict[str, float]) -> dict:
    """Precompute all fixed tables (call once before the MC loop)."""
    return {"ko": build_ko_table(elos)}


def simulate_once(
    elos: dict[str, float],
    rng: np.random.Generator,
    tables: dict,
) -> dict[str, int]:
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
    ko_table = tables["ko"]
    reached = {team: 0 for group in GROUPS.values() for team in group}

    # --- Group stage (all 72 matches in one vectorised batch) ---
    group_results   = simulate_all_groups(GROUPS, elos, rng)
    group_finishers = {}
    third_place_teams = []

    for letter, ranked in group_results.items():
        group_finishers[letter] = {i + 1: ranked[i]["team"] for i in range(4)}
        third_entry = ranked[2].copy()
        third_entry["group_letter"] = letter
        third_place_teams.append(third_entry)

    # --- Third-place selection ---
    advancing_8, _ = select_third_place(third_place_teams)
    advancing_set = {t["team"] for t in advancing_8}

    for letter, finishers in group_finishers.items():
        reached[finishers[1]] = 1
        reached[finishers[2]] = 1
        if finishers[3] in advancing_set:
            reached[finishers[3]] = 1

    # --- Build R32 bracket ---
    third_assignments = assign_third_place(advancing_8, group_finishers)
    r32_matchups = build_r32_matchups(group_finishers, third_assignments)

    # --- Simulate knockout rounds ---
    r32_w  = _sim_round(r32_matchups,                    ko_table, elos, rng, reached, exit_r=1, adv_r=2)
    r16_w  = _sim_round(_pair(r32_w,  R16_PAIRS),        ko_table, elos, rng, reached, exit_r=2, adv_r=3)
    qf_w   = _sim_round(_pair(r16_w,  QF_PAIRS),         ko_table, elos, rng, reached, exit_r=3, adv_r=4)
    sf_w   = _sim_round(_pair(qf_w,   SF_PAIRS),         ko_table, elos, rng, reached, exit_r=4, adv_r=5)

    a, b   = sf_w[0], sf_w[1]
    winner = simulate_knockout(a, b, ko_table, rng)
    loser  = b if winner == a else a
    reached[loser]  = 5
    reached[winner] = 6

    return reached


def _sim_round(matchups, ko_table, elos, rng, reached, exit_r, adv_r):
    winners = []
    for a, b in matchups:
        w = simulate_knockout(a, b, ko_table, rng)
        loser = b if w == a else a
        reached[loser] = exit_r
        reached[w]     = adv_r
        winners.append(w)
    return winners


def _pair(winners, pairs):
    return [(winners[i], winners[j]) for i, j in pairs]
