# 2026 FIFA World Cup Simulator

Monte Carlo tournament simulator for the 2026 FIFA World Cup (48 teams, 12 groups). Given Elo ratings, it runs tens of thousands of full tournament simulations and outputs each team's probability of reaching every round.

## Quick Start

```bash
pip install numpy
python simulate.py
```

Default: 50,000 simulations (~14 seconds). Results print to stdout.

### Options

```
--n N        Number of simulations (default: 50000)
--seed SEED  Random seed for reproducibility
--top N      Show only top N teams by win probability
```

## Output

```
Team                      Groups       R32       R16        QF        SF     Final       Win
--------------------------------------------------------------------------------------------
Argentina                   99.6%      75.5%      63.5%      47.7%      32.5%      20.5%
Spain                       99.9%      77.7%      56.8%      46.3%      31.9%      19.9%
...
```

Each column is the probability of **reaching** that round (i.e., advancing past the previous one).

## Updating Elo Ratings

Edit `data/elos.py`. Current values are from [eloratings.net](https://www.eloratings.net/2026_World_Cup), updated mid-tournament June 2026.

---

## Methodology

### 1. Win Expectancy

For every match between team A (Elo `E_A`) and team B (Elo `E_B`), the win expectancy for A is:

```
W_A = 1 / (1 + 10^((E_B - E_A) / 400))
W_B = 1 - W_A
```

All matches are treated as neutral-ground (no home advantage adjustment).

---

### 2. Expected Goals (Csató 2025)

Win expectancy is converted to expected goals per team using the two-regime polynomial from Csató (2025, arXiv 2502.08565), fit on ~40,000 international matches.

**Regime 1 — W ≤ 0.9:**
```
λ = 3.90388·W⁴ − 0.58486·W³ − 2.98315·W² + 3.13160·W + 0.33193
```

**Regime 2 — W > 0.9** (let x = W − 0.9):
```
λ = 308097.45501·x⁴ − 42803.04696·x³ + 2116.35304·x² − 9.61869·x + 2.86899
```

The same polynomial applies to both teams — team B uses `W_B = 1 − W_A`. At equal strength (W = 0.5), both teams get λ ≈ 1.32 goals. The boundary at W = 0.9 is continuous (λ ≈ 2.87 from both sides).

---

### 3. Score Grid with Dixon-Coles Correction

Rather than sampling win/draw/loss first and then fitting a scoreline to it, the model builds a full **9×9 joint score-probability grid** (goals 0–8 for each team) which covers >99.9% of probability mass at typical λ values.

**Raw cell probability:**
```
P(i, j) = Poisson(i | λ_A) × Poisson(j | λ_B)
```

**Dixon-Coles τ correction** on the four low-score cells (ρ = −0.1):
```
τ(0,0) = 1 − λ_A · λ_B · ρ
τ(1,0) = 1 + λ_B · ρ
τ(0,1) = 1 + λ_A · ρ
τ(1,1) = 1 − ρ
τ(i,j) = 1  for all other cells
```

The correction (ρ < 0) slightly reduces 0-0 and 1-1 draws and boosts 1-0 / 0-1 results, matching the empirical under-representation of draws at low scores in international football.

The full grid is normalised to sum to 1 after applying τ. A scoreline is then sampled directly from the 81-cell distribution — no rejection sampling needed.

---

### 4. Win / Draw / Loss Probabilities

Win, draw, and loss probabilities are derived by summing over the relevant grid cells:

```
P(A wins) = Σ P(i,j)  for i > j
P(draw)   = Σ P(i,j)  for i = j
P(B wins) = Σ P(i,j)  for i < j
```

These are used implicitly (the scoreline sampled from the grid already encodes the outcome). For diagnostic purposes, at equal Elo (W = 0.5, λ ≈ 1.32 each), the model produces roughly:

| Outcome | Probability |
|---------|-------------|
| Win     | ~46%        |
| Draw    | ~26%        |
| Loss    | ~28%        |

(slight asymmetry because Poisson is discrete; exact values depend on λ)

---

### 5. Knockout Matches

In knockout rounds, draws are not allowed. The win probability for A is:

```
P(A wins knockout) = P(A wins) + 0.5 × P(draw)
```

The 50% split on draws models extra time and penalties as a coin flip, which is a reasonable approximation (historically ~50/50 in penalty shootouts).

Knockout win probabilities for all 48×48 team pairs are **precomputed once** before the Monte Carlo loop and stored in a lookup table, so each knockout match during simulation is an O(1) lookup rather than a grid rebuild.

---

### 6. Group Stage

All 72 group matches (12 groups × 6 round-robin games) are simulated in a **single vectorised numpy call** per tournament iteration. Standings are computed per group using FIFA's tiebreaker cascade:

1. Points (head-to-head among tied teams)
2. Goal difference (head-to-head)
3. Goals scored (head-to-head)
4. Overall goal difference
5. Overall goals scored
6. Random draw (proxy for fair play / FIFA ranking, which we don't model)

---

### 7. Third-Place Advancement

All 12 third-place finishers are ranked across groups by points → goal difference → goals scored → random. The best 8 advance to the Round of 32.

---

### 8. Bracket

The Round of 32 has 16 matches. Slots for group winners and runners-up are fixed. The 8 advancing third-place teams are placed using FIFA's Annex C rules — each slot lists eligible groups, ensuring no same-group rematches in the first knockout round.

The full bracket tree then pairs adjacent match winners through R16 → QF → SF → Final.

---

## Performance

| Stage | Detail |
|-------|--------|
| Group stage | 72 matches batched in one numpy call per simulation |
| Knockout | O(1) lookup from precomputed 48×48 win-prob table |
| Total | ~14s for 50,000 simulations on a single CPU core |

---

## File Structure

```
wc-sim/
├── simulate.py          # entry point
├── data/
│   └── elos.py          # team Elo ratings (edit these)
└── src/
    ├── groups.py        # group compositions (12 groups, 4 teams each)
    ├── match.py         # Csató λ, Dixon-Coles grid, KO table
    ├── group_stage.py   # round-robin tallying + FIFA tiebreakers
    ├── third_place.py   # select best 8 third-place teams
    ├── bracket.py       # Annex C placement + bracket tree definition
    └── tournament.py    # orchestrate one full simulation
```
