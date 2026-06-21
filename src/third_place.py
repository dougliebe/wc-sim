import random


def select_third_place(third_place_teams: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Given 12 third-place team dicts (each with pts, gd, gf, group_letter),
    select the best 8 and return (advancing_8, advancing_group_letters).
    Ranking: points → goal diff → goals scored → random draw.
    """
    ranked = sorted(
        third_place_teams,
        key=lambda s: (s["pts"], s["gd"], s["gf"], random.random()),
        reverse=True,
    )
    advancing = ranked[:8]
    group_letters = sorted([t["group_letter"] for t in advancing])
    return advancing, group_letters
