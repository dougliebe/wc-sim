import numpy as np

BASE_GOALS = 1.25
GOALS_ELO_EXPONENT = 0.5
DRAW_SCALE = 0.27


def win_prob(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def match_probs(elo_a: float, elo_b: float) -> tuple[float, float, float]:
    p_win_base = win_prob(elo_a, elo_b)
    p_draw = DRAW_SCALE * (1.0 - 2.0 * abs(p_win_base - 0.5))
    remaining = 1.0 - p_draw
    p_win = remaining * p_win_base
    p_loss = remaining * (1.0 - p_win_base)
    return p_win, p_draw, p_loss


def simulate_group_matches_vectorized(
    team_pairs: list[tuple[str, str]],
    elos: dict[str, float],
    rng: np.random.Generator,
) -> list[tuple[int, int]]:
    """
    Simulate a batch of matches simultaneously using vectorized numpy.
    Returns list of (goals_a, goals_b) — no rejection sampling.
    """
    n = len(team_pairs)
    elo_a = np.array([elos[a] for a, _ in team_pairs])
    elo_b = np.array([elos[b] for _, b in team_pairs])

    p_win_base = 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))
    p_draw = DRAW_SCALE * (1.0 - 2.0 * np.abs(p_win_base - 0.5))
    remaining = 1.0 - p_draw
    p_win = remaining * p_win_base
    p_loss = remaining * (1.0 - p_win_base)

    # Sample outcomes
    outcomes = np.empty(n, dtype=np.int8)  # 0=win, 1=draw, 2=loss
    u = rng.random(n)
    outcomes[:] = 2  # default loss
    outcomes[u < p_win + p_draw] = 1  # draw
    outcomes[u < p_win] = 0  # win

    # Sample Poisson goals
    ratio = elo_a / elo_b
    lam_a = BASE_GOALS * (ratio ** GOALS_ELO_EXPONENT)
    lam_b = BASE_GOALS * ((1.0 / ratio) ** GOALS_ELO_EXPONENT)
    ga = rng.poisson(lam_a).astype(np.int32)
    gb = rng.poisson(lam_b).astype(np.int32)

    # Adjust scorelines to match outcomes — no rejection sampling needed
    win_mask  = outcomes == 0
    draw_mask = outcomes == 1
    loss_mask = outcomes == 2

    # Win: ensure ga > gb
    fix = win_mask & (ga <= gb)
    ga[fix] = gb[fix] + 1

    # Draw: set gb = ga
    gb[draw_mask] = ga[draw_mask]

    # Loss: ensure gb > ga
    fix = loss_mask & (gb <= ga)
    gb[fix] = ga[fix] + 1

    return list(zip(ga.tolist(), gb.tolist()))


def simulate_knockout(elo_a: float, elo_b: float, rng: np.random.Generator) -> str:
    p = win_prob(elo_a, elo_b)
    return "A" if rng.random() < p else "B"
