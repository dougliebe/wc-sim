"""
Match probability and scoreline simulation.

Goal expectation: Csató 2025 (arXiv 2502.08565), fit on ~40k international matches.
Low-score correction: Dixon-Coles τ, ρ ≈ -0.1.
Score grid enumerated 0–8 × 0–8 (covers >99.9% of probability mass at typical λ ~1.3).

A pairwise knockout win-probability table is precomputed once from all team Elos
so that in-simulation knockout matches are O(1) lookups.
"""
import math
import numpy as np

MAX_G = 8
_GOALS = np.arange(MAX_G + 1, dtype=float)                    # (9,)
_LOG_FACT = np.array([math.lgamma(k + 1) for k in range(MAX_G + 1)])  # log k!
_DRAW_MASK = np.equal.outer(np.arange(MAX_G + 1), np.arange(MAX_G + 1))  # (9,9) bool
_WIN_MASK  = np.greater.outer(np.arange(MAX_G + 1), np.arange(MAX_G + 1))  # (9,9) bool

DC_RHO = -0.1


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _csato_lambda(w: np.ndarray) -> np.ndarray:
    """Win expectancy W → expected goals λ (Csató 2025, neutral ground). Vectorised."""
    w = np.asarray(w, dtype=float)
    lo_mask = w <= 0.9
    x = np.where(lo_mask, w, w - 0.9)

    lam_lo = (3.90388 * w**4
              - 0.58486 * w**3
              - 2.98315 * w**2
              + 3.13160 * w
              + 0.33193)

    lam_hi = (308097.45501 * x**4
              -  42803.04696 * x**3
              +   2116.35304 * x**2
              -      9.61869 * x
              +      2.86899)

    return np.clip(np.where(lo_mask, lam_lo, lam_hi), 0.01, None)


def _poisson_pmf_batch(lam: np.ndarray) -> np.ndarray:
    """Poisson PMF for goals 0..MAX_G for N lambda values. Returns (N, 9)."""
    log_pmf = _GOALS[None, :] * np.log(lam[:, None]) - lam[:, None] - _LOG_FACT[None, :]
    return np.exp(log_pmf)


def _score_grids(lam_a: np.ndarray, lam_b: np.ndarray) -> np.ndarray:
    """
    Joint score-probability grids for N matches. Returns (N, 9, 9).
    Axis 1 = goals_a, axis 2 = goals_b.
    """
    pmf_a = _poisson_pmf_batch(lam_a)  # (N, 9)
    pmf_b = _poisson_pmf_batch(lam_b)  # (N, 9)
    grid = pmf_a[:, :, None] * pmf_b[:, None, :]  # (N, 9, 9)

    # Dixon-Coles τ correction for four low-score cells
    grid[:, 0, 0] *= 1.0 - lam_a * lam_b * DC_RHO
    grid[:, 1, 0] *= 1.0 + lam_b * DC_RHO
    grid[:, 0, 1] *= 1.0 + lam_a * DC_RHO
    grid[:, 1, 1] *= 1.0 - DC_RHO

    grid /= grid.sum(axis=(1, 2), keepdims=True)
    return grid


def _win_expectancies(elo_a: np.ndarray, elo_b: np.ndarray):
    """Returns (w_a, w_b) from Elo arrays."""
    w_a = 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))
    return w_a, 1.0 - w_a


# ---------------------------------------------------------------------------
# Pre-built pairwise knockout table
# ---------------------------------------------------------------------------

def build_ko_table(elos: dict[str, float]) -> dict[tuple[str, str], float]:
    """
    Precompute P(A beats B in knockout) for every ordered team pair.
    Called once at simulation startup. Returns dict keyed by (team_a, team_b).
    Draws go 50/50 (extra time / penalties modelled as coin flip).
    """
    teams = list(elos.keys())
    n = len(teams)
    elo_arr = np.array([elos[t] for t in teams], dtype=float)

    # All pairwise win expectancies: (n*n,)
    idx_a, idx_b = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    ea = elo_arr[idx_a.ravel()]
    eb = elo_arr[idx_b.ravel()]

    w_a, w_b = _win_expectancies(ea, eb)
    lam_a = _csato_lambda(w_a)
    lam_b = _csato_lambda(w_b)

    grids = _score_grids(lam_a, lam_b)          # (n*n, 9, 9)
    p_win  = grids[:, _WIN_MASK].sum(axis=1)     # (n*n,)
    p_draw = grids[:, _DRAW_MASK].sum(axis=1)    # (n*n,)
    p_win_ko = p_win + 0.5 * p_draw              # (n*n,)

    table = {}
    for k, (i, j) in enumerate(zip(idx_a.ravel(), idx_b.ravel())):
        table[(teams[i], teams[j])] = float(p_win_ko[k])
    return table


# ---------------------------------------------------------------------------
# Group-stage match simulation (draws allowed, vectorised)
# ---------------------------------------------------------------------------

def simulate_group_matches_vectorized(
    team_pairs: list[tuple[str, str]],
    elos: dict[str, float],
    rng: np.random.Generator,
) -> list[tuple[int, int]]:
    """
    Simulate group-stage matches using Csató + Dixon-Coles score grid.
    Returns (goals_a, goals_b) per match.
    """
    n = len(team_pairs)
    elo_a = np.array([elos[a] for a, _ in team_pairs], dtype=float)
    elo_b = np.array([elos[b] for _, b in team_pairs], dtype=float)

    w_a, w_b = _win_expectancies(elo_a, elo_b)
    lam_a = _csato_lambda(w_a)
    lam_b = _csato_lambda(w_b)

    grid = _score_grids(lam_a, lam_b)  # (N, 9, 9)

    # Sample one scoreline per match from the flattened grid
    flat = grid.reshape(n, -1)          # (N, 81)
    cum  = np.cumsum(flat, axis=1)
    u    = rng.random(n)[:, None]
    indices = (cum < u).sum(axis=1)    # (N,)

    goals_a = (indices // (MAX_G + 1)).astype(np.int32)
    goals_b = (indices  % (MAX_G + 1)).astype(np.int32)

    return list(zip(goals_a.tolist(), goals_b.tolist()))


# ---------------------------------------------------------------------------
# Knockout (O(1) lookup, no grid rebuild)
# ---------------------------------------------------------------------------

def simulate_knockout(
    team_a: str,
    team_b: str,
    ko_table: dict[tuple[str, str], float],
    rng: np.random.Generator,
) -> str:
    """Return the winning team name. Uses precomputed knockout table."""
    p = ko_table[(team_a, team_b)]
    return team_a if rng.random() < p else team_b
