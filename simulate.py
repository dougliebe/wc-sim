#!/usr/bin/env python3
"""
2026 FIFA World Cup Monte Carlo Simulator
Usage: python simulate.py [--n N] [--seed SEED]
"""
import argparse
import sys
from collections import defaultdict
import numpy as np

from data.elos import ELOS
from src.tournament import simulate_once, build_tables

ROUND_NAMES = {
    0: "Group Stage Exit",
    1: "R32 Exit",
    2: "R16 Exit",
    3: "QF Exit",
    4: "SF Exit",
    5: "Runner-Up",
    6: "Champion",
}

ROUND_HEADERS = ["Groups", "R32", "R16", "QF", "SF", "Final", "Win"]


def run(n: int, seed: int | None) -> dict[str, list[float]]:
    rng = np.random.default_rng(seed)
    print("Building lookup tables...", file=sys.stderr)
    tables = build_tables(ELOS)
    counts = defaultdict(lambda: [0] * 7)  # team -> [count_reached_round_0..6]

    for i in range(n):
        if i % 5000 == 0 and i > 0:
            print(f"  {i}/{n} simulations...", file=sys.stderr)
        result = simulate_once(ELOS, rng, tables)
        for team, round_reached in result.items():
            for r in range(round_reached + 1):
                counts[team][r] += 1

    probs = {team: [c / n for c in cnts] for team, cnts in counts.items()}
    return probs


def print_table(probs: dict[str, list[float]], top_n: int | None = None) -> None:
    # Sort by championship probability descending
    sorted_teams = sorted(probs.items(), key=lambda x: x[1][6], reverse=True)
    if top_n:
        sorted_teams = sorted_teams[:top_n]

    col_w = 10
    name_w = 22
    header = f"{'Team':<{name_w}}" + "".join(f"{h:>{col_w}}" for h in ROUND_HEADERS)
    print(header)
    print("-" * (name_w + col_w * len(ROUND_HEADERS)))

    for team, p in sorted_teams:
        # p[0] = made it past group (R32+), p[6] = champion
        # Display: P(advance from group), P(make R16), P(make QF), P(make SF), P(make Final), P(Win)
        row_vals = [
            p[1],   # reached R32 (advanced from group)
            p[2],   # reached R16
            p[3],   # reached QF
            p[4],   # reached SF
            p[5],   # reached Final
            p[6],   # won
        ]
        # First column: P(group exit) implicitly = 1-p[1]
        pct_str = "".join(f"{v*100:>{col_w}.1f}%" for v in row_vals)
        # Squeeze to fit: show group advance % first
        row = f"{team:<{name_w}}" + pct_str
        print(row)


def main():
    parser = argparse.ArgumentParser(description="2026 World Cup Simulator")
    parser.add_argument("--n", type=int, default=50_000, help="Number of simulations (default 50000)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--top", type=int, default=None, help="Show only top N teams by win probability")
    args = parser.parse_args()

    print(f"Running {args.n:,} simulations...", file=sys.stderr)
    probs = run(args.n, args.seed)
    print(f"\n2026 World Cup Probabilities ({args.n:,} simulations)\n")
    col_w = 10
    name_w = 22
    header = f"{'Team':<{name_w}}" + "".join(f"{h:>{col_w}}" for h in ROUND_HEADERS)
    print(header)
    print("-" * (name_w + col_w * len(ROUND_HEADERS)))
    sorted_teams = sorted(probs.items(), key=lambda x: x[1][6], reverse=True)
    if args.top:
        sorted_teams = sorted_teams[: args.top]
    for team, p in sorted_teams:
        row_vals = [p[1], p[2], p[3], p[4], p[5], p[6]]
        row = f"{team:<{name_w}}" + "".join(f"{v*100:>{col_w}.1f}%" for v in row_vals)
        print(row)


if __name__ == "__main__":
    main()
