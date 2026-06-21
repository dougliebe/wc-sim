"""
Tests for third-place tiebreaker logic (select_third_place) and
Annex C bracket placement (assign_third_place).

FIFA official third-place ranking criteria:
  1. Points
  2. Goal difference
  3. Goals scored
  4. Team conduct score  ← NOT IMPLEMENTED (we use random)
  5. FIFA world ranking  ← NOT IMPLEMENTED (we use random)
  6. Drawing of lots

Our implementation: pts → GD → GF → random
"""

import random
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from collections import defaultdict
from src.third_place import select_third_place
from src.bracket import assign_third_place, R32_SLOTS


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_team(group, pts, gd, gf):
    return {"group_letter": group, "team": f"Team{group}", "pts": pts, "gd": gd, "gf": gf}


def make_group_finishers(groups):
    """Build a minimal group_finishers dict for the given group letters."""
    gf = {}
    for g in groups:
        gf[g] = {
            1: f"1st{g}", 2: f"2nd{g}", 3: f"3rd{g}", 4: f"4th{g}"
        }
    return gf


ALL_GROUPS = list("ABCDEFGHIJKL")


# ── select_third_place: deterministic cases ────────────────────────────────────

def test_top8_by_points():
    """8 teams with clearly distinct pts should advance by pts alone."""
    teams = [make_team(g, 10 - i, 0, 0) for i, g in enumerate(ALL_GROUPS)]
    advancing, letters = select_third_place(teams)
    assert len(advancing) == 8
    pts_advancing = sorted([t["pts"] for t in advancing], reverse=True)
    assert pts_advancing[0] == 10
    assert pts_advancing[-1] == 3  # top 8 of 12 (pts 10..3, rest 2,1,0,−1 impossible)
    # Check exactly the top-8 pts teams advanced
    assert all(t["pts"] >= 3 for t in advancing)


def test_top8_by_goal_difference():
    """When pts are tied, teams should be separated by GD."""
    # All 12 teams with same pts, different GD
    teams = [make_team(g, 4, i - 5, 5) for i, g in enumerate(ALL_GROUPS)]
    # GD: A=-5, B=-4, ..., L=6 → top 8 are E(0),F(1),...,L(6) = 8 teams with GD >= 0? No.
    # Actually: i=0→A GD=-5, i=11→L GD=6. Top 8 by GD: E(0),F(1),G(2),H(3),I(4),J(5),K(6 - wait)
    # i=4→E gd=-1, i=5→F gd=0, ... i=11→L gd=6. Top 8: E(-1) through L(6) = groups E-L
    advancing, letters = select_third_place(teams)
    assert len(advancing) == 8
    advancing_gd = sorted([t["gd"] for t in advancing], reverse=True)
    # All advancing teams must have GD >= -1 (the 8th best)
    assert all(t["gd"] >= -1 for t in advancing)


def test_top8_by_goals_scored():
    """When pts and GD tied, teams should be separated by GF."""
    teams = [make_team(g, 4, 0, i) for i, g in enumerate(ALL_GROUPS)]
    advancing, letters = select_third_place(teams)
    assert len(advancing) == 8
    # Top 8 GF are groups E(4) through L(11)
    assert all(t["gf"] >= 4 for t in advancing)


def test_returns_exactly_8():
    teams = [make_team(g, 3, 0, 3) for g in ALL_GROUPS]
    advancing, letters = select_third_place(teams)
    assert len(advancing) == 8
    assert len(letters) == 8


def test_group_letters_sorted():
    teams = [make_team(g, 3, 0, 3) for g in ALL_GROUPS]
    _, letters = select_third_place(teams)
    assert letters == sorted(letters)


def test_returns_correct_structure():
    teams = [make_team(g, 3, 1, 4) for g in ALL_GROUPS]
    advancing, letters = select_third_place(teams)
    for t in advancing:
        assert "group_letter" in t
        assert "pts" in t
        assert "gd" in t
        assert "gf" in t


# ── select_third_place: tiebreaker frequency analysis ─────────────────────────

def test_tiebreaker_frequency():
    """
    Run many trials with all 12 teams equal across all criteria.
    Measure how often each position is filled by different groups (should be ~uniform).
    Also track how often a pts-only decision vs GD vs GF vs random decides the 8th spot.
    """
    N = 10_000
    # 12 teams all identical — all decisions by random
    teams = [make_team(g, 4, 2, 6) for g in ALL_GROUPS]

    selection_counts = defaultdict(int)
    for _ in range(N):
        advancing, letters = select_third_place(teams)
        for t in advancing:
            selection_counts[t["group_letter"]] += 1

    # With all teams equal, each group should advance ~8/12 = 66.7% of the time
    for g in ALL_GROUPS:
        rate = selection_counts[g] / N
        # Allow generous tolerance for stochastic test
        assert 0.55 < rate < 0.80, f"Group {g} advance rate {rate:.3f} out of expected ~0.667"


def _which_criterion_decided(teams_sorted):
    """
    Given 12 teams sorted by our algorithm (pts desc, gd desc, gf desc, random),
    determine which criterion separated rank 8 from rank 9.
    Returns: 'pts' | 'gd' | 'gf' | 'random'
    """
    t8 = teams_sorted[7]
    t9 = teams_sorted[8]
    if t8["pts"] != t9["pts"]:
        return "pts"
    if t8["gd"] != t9["gd"]:
        return "gd"
    if t8["gf"] != t9["gf"]:
        return "gf"
    return "random"


def test_criterion_usage_realistic():
    """
    Simulate realistic third-place scenarios (random pts/gd/gf drawn from
    plausible distributions) and count how often each criterion decides the
    8th spot. Prints a summary.
    """
    N = 50_000
    criterion_counts = defaultdict(int)

    for _ in range(N):
        teams = []
        for g in ALL_GROUPS:
            pts = random.choice([0, 1, 3, 4, 6, 7])
            gd = random.randint(-5, 5)
            gf = random.randint(0, 9)
            teams.append(make_team(g, pts, gd, gf))

        # Sort the same way select_third_place does (minus the random tie, capture sort key)
        sorted_teams = sorted(
            teams,
            key=lambda s: (s["pts"], s["gd"], s["gf"]),
            reverse=True,
        )
        criterion = _which_criterion_decided(sorted_teams)
        criterion_counts[criterion] += 1

    total = sum(criterion_counts.values())
    print("\n=== Tiebreaker frequency at 8th/9th boundary ===")
    for k in ["pts", "gd", "gf", "random"]:
        pct = criterion_counts[k] / total * 100
        print(f"  {k:8s}: {pct:5.1f}%")

    # At least pts must be most common decider in realistic scenarios
    assert criterion_counts["pts"] > criterion_counts["random"]


# ── assign_third_place: Annex C slot assignment ───────────────────────────────

def _make_advancing_8(group_letters):
    return [{"group_letter": g, "team": f"Team3{g}"} for g in group_letters]


def test_assign_all_slots_filled():
    """Every one of the 8 third-place slots must be filled."""
    advancing = _make_advancing_8(list("ABCDEFGH"))
    gf = make_group_finishers(ALL_GROUPS)
    result = assign_third_place(advancing, gf)
    assert len(result) == 8
    third_slot_ids = {s["id"] for s in R32_SLOTS if s["eligible_3rd"] is not None}
    assert set(result.keys()) == third_slot_ids


def test_assign_each_team_once():
    """Each third-place team is used exactly once."""
    advancing = _make_advancing_8(list("CDEFGHIJ"))
    gf = make_group_finishers(ALL_GROUPS)
    result = assign_third_place(advancing, gf)
    teams_assigned = list(result.values())
    assert len(teams_assigned) == len(set(teams_assigned)), "Duplicate team in assignments"


def test_assign_eligibility_respected():
    """Each slot only gets a team from an eligible group."""
    slot_by_id = {s["id"]: s for s in R32_SLOTS if s["eligible_3rd"] is not None}
    # Try several combinations
    for combo in [
        list("ABCDEFGH"),
        list("CDEFGHIJ"),
        list("EFGHIJKL"),
        list("ABCFGHIJ"),
    ]:
        advancing = _make_advancing_8(combo)
        gf = make_group_finishers(ALL_GROUPS)
        result = assign_third_place(advancing, gf)
        for slot_id, team in result.items():
            slot = slot_by_id[slot_id]
            # Extract the group letter from the team name (e.g., "Team3E" → "E")
            group_letter = team.replace("Team3", "")
            assert group_letter in slot["eligible_3rd"], (
                f"Slot {slot_id} (eligible: {slot['eligible_3rd']}) got team from group {group_letter}"
            )


def test_assign_no_same_group_collision():
    """No slot can be filled by a team from a group that already fills another slot in the same match."""
    # This is guaranteed structurally since each group provides one team and each slot gets one team.
    advancing = _make_advancing_8(list("ABCDEFGH"))
    gf = make_group_finishers(ALL_GROUPS)
    result = assign_third_place(advancing, gf)
    used_groups = set()
    for slot_id, team in result.items():
        group_letter = team.replace("Team3", "")
        assert group_letter not in used_groups, f"Group {group_letter} assigned to multiple slots"
        used_groups.add(group_letter)


def test_assign_operator_precedence_fix():
    """
    Regression test for the bug: `slot["eligible_3rd"] & advancing_letters - used`
    which due to Python precedence was parsed as `eligible_3rd & (advancing_letters - used)`.
    Fixed to: `(slot["eligible_3rd"] & advancing_letters) - used`.
    Verify with a case where the old code would fail.
    """
    # Construct a scenario where the difference matters:
    # Use groups A,B,C,D,E,F,G,H advancing
    # Slot 8 eligible: {A,E,H,I,J} → intersection with advancing = {A,E,H}
    # If "used" contains {A,E} then:
    #   Old: eligible_3rd & (advancing - used) = {A,E,H,I,J} & {B,C,D,F,G,H} = {H}  (correct result, different logic)
    #   Actually the old bug DOES give {H} but for slots where the intersection is empty first it breaks.
    # Better test: confirm we can always assign all 8 slots without KeyError or wrong team.
    for _ in range(100):
        combo = sorted(random.sample(ALL_GROUPS, 8))
        advancing = _make_advancing_8(combo)
        gf = make_group_finishers(ALL_GROUPS)
        result = assign_third_place(advancing, gf)
        assert len(result) == 8, f"Not all slots filled for combo {combo}"
        # Verify eligibility
        slot_by_id = {s["id"]: s for s in R32_SLOTS if s["eligible_3rd"] is not None}
        for slot_id, team in result.items():
            g = team.replace("Team3", "")
            assert g in slot_by_id[slot_id]["eligible_3rd"], (
                f"Slot {slot_id} got ineligible group {g} for combo {combo}"
            )


def test_assign_stress_all_combinations():
    """
    Test all possible C(12,8)=495 combinations of advancing groups.
    Every combination must produce a valid assignment.
    """
    from itertools import combinations
    slot_by_id = {s["id"]: s for s in R32_SLOTS if s["eligible_3rd"] is not None}
    gf = make_group_finishers(ALL_GROUPS)
    failures = []

    for combo in combinations(ALL_GROUPS, 8):
        advancing = _make_advancing_8(list(combo))
        try:
            result = assign_third_place(advancing, gf)
        except Exception as e:
            failures.append((combo, f"Exception: {e}"))
            continue
        if len(result) != 8:
            failures.append((combo, f"Only {len(result)} slots filled"))
            continue
        used = set()
        for slot_id, team in result.items():
            g = team.replace("Team3", "")
            if g in used:
                failures.append((combo, f"Duplicate group {g}"))
                break
            used.add(g)
            if g not in slot_by_id[slot_id]["eligible_3rd"]:
                failures.append((combo, f"Slot {slot_id} got ineligible group {g}"))
                break

    if failures:
        print(f"\n=== assign_third_place failures ({len(failures)}/495) ===")
        for combo, reason in failures[:20]:
            print(f"  {''.join(combo)}: {reason}")

    assert len(failures) == 0, (
        f"{len(failures)}/495 group combinations failed assignment. "
        f"First failure: {''.join(failures[0][0])} — {failures[0][1]}"
    )


# ── FIFA rule gap documentation ────────────────────────────────────────────────

def test_document_missing_criteria():
    """
    Documents the gap between our implementation and official FIFA rules.
    This test always passes but prints a clear warning.

    Official FIFA WC 2026 third-place ranking (Article 32.4):
      1. Points
      2. Goal difference
      3. Goals scored
      4. Team conduct score (yellow/red card deductions)
      5. FIFA world ranking (higher rank = better)
      6. Drawing of lots

    Our implementation uses random after GF, skipping criteria 4 and 5.
    """
    print("\n=== FIFA Third-Place Tiebreaker Gap ===")
    print("  Criterion 4 (team conduct score): NOT IMPLEMENTED — using random")
    print("  Criterion 5 (FIFA world ranking):  NOT IMPLEMENTED — using random")
    print("  Impact: At pts+GD+GF ties, we randomly pick instead of using conduct/ranking.")
    print("  Frequency: see test_criterion_usage_realistic() for how often this matters.")
    # Passes always — this is a documentation test
    assert True
