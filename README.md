# 2026 FIFA World Cup Simulator

Monte Carlo tournament simulator for the 2026 FIFA World Cup (48 teams, 12 groups). Given Elo ratings, it runs tens of thousands of full tournament simulations and outputs each team's probability of reaching every round.

## Quick Start

```bash
pip install numpy
python simulate.py
```

Default: 50,000 simulations. Results print to stdout.

### Options

```
--n N        Number of simulations (default: 50000)
--seed SEED  Random seed for reproducibility
--top N      Show only top N teams by win probability
```

Example:
```bash
python simulate.py --n 100000 --seed 1 --top 20
```

## Output

```
Team                      Groups       R32       R16        QF        SF     Final       Win
--------------------------------------------------------------------------------------------
Argentina                   99.2%      76.3%      66.1%      52.4%      39.1%      28.4%
Spain                       98.4%      65.6%      48.2%      35.5%      22.7%      12.4%
...
```

Columns are the probability of **reaching** that round (i.e., advancing past the previous one).

## Updating Elo Ratings

Edit `data/elos.py`. Current values are approximate pre-tournament ratings from [World Football Elo Ratings](https://www.eloratings.net/). Replace with current values for best accuracy.

## Methodology

### Elo → Match Probabilities

Win probability for team A vs B:

```
p_win_base = 1 / (1 + 10^((elo_B - elo_A) / 400))
```

Draw probability peaks at ~27% when teams are equally rated and shrinks as the gap grows:

```
p_draw = 0.27 × (1 - 2 × |p_win_base - 0.5|)
```

The remaining probability is split proportionally into win and loss.

### Scoreline Simulation

Goals are sampled from a Poisson distribution scaled by the Elo ratio:

```
λ_A = 1.25 × (elo_A / elo_B)^0.5
λ_B = 1.25 × (elo_B / elo_A)^0.5
```

The sampled scoreline is adjusted (without rejection sampling) to match the already-drawn outcome (win/draw/loss), preserving the distributional shape while avoiding infinite loops.

### Group Stage Tiebreakers

FIFA's official cascade, applied to simulated scorelines:

1. Points in head-to-head matches (among tied teams only)
2. Goal difference in head-to-head matches
3. Goals scored in head-to-head matches
4. Overall goal difference
5. Overall goals scored
6. Random draw (stand-in for fair play / FIFA ranking)

### Third-Place Advancement

All 12 group third-place teams are ranked by points → goal difference → goals scored → random. The best 8 advance to the Round of 32.

### Bracket Structure

The Round of 32 has 16 fixed slots for group winners and runners-up. The 8 advancing third-place teams are assigned to the remaining 8 slots using FIFA's Annex C rules — each slot specifies which groups are eligible, preventing same-group rematches. The knockout bracket then pairs:

- **R16**: adjacent R32 match winners (M1vsM2, M3vsM4, …)
- **QF**: adjacent R16 winners
- **SF/Final**: standard single-elimination tree

### Performance

~33 seconds for 50,000 simulations on a single CPU core (vectorized numpy group stage).

## File Structure

```
wc-sim/
├── simulate.py          # entry point
├── data/
│   └── elos.py          # team Elo ratings (edit these)
└── src/
    ├── groups.py        # group compositions
    ├── match.py         # Elo→probabilities, vectorized scoreline sampling
    ├── group_stage.py   # round-robin simulation + tiebreakers
    ├── third_place.py   # select best 8 third-place teams
    ├── bracket.py       # Annex C placement + bracket tree
    └── tournament.py    # orchestrate one full simulation
```
