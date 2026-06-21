"""
Round of 32 bracket structure and Annex C third-place placement.

R32 slots (group positions fixed; third-place slot filled by Annex C):
    M1:  1E  vs  3[ABCDF]
    M2:  1I  vs  3[CDFGH]
    M3:  2A  vs  2B
    M4:  1F  vs  2C
    M5:  2K  vs  2L
    M6:  1H  vs  2J
    M7:  1D  vs  3[BEFIJ]
    M8:  1G  vs  3[AEHIJ]
    M9:  1C  vs  2F
    M10: 2E  vs  2I
    M11: 1A  vs  3[CEFHI]
    M12: 1L  vs  3[EHIJK]
    M13: 1J  vs  2H
    M14: 2D  vs  2G
    M15: 1B  vs  3[EFGIJ]
    M16: 1K  vs  3[DEIJL]

Bracket tree (winner of Mi plays winner of Mj):
    R16: (M1,M2), (M3,M4), (M5,M6), (M7,M8),
         (M9,M10),(M11,M12),(M13,M14),(M15,M16)
    QF:  (R16_1,R16_2),(R16_3,R16_4),(R16_5,R16_6),(R16_7,R16_8)
    SF:  (QF_1,QF_2),(QF_3,QF_4)
    F:   (SF_1,SF_2)
"""

# Each R32 match: (slot_key_for_group_position, eligible_groups_for_3rd_place_slot | None)
# None means the slot is a fixed 2nd-place pairing, no third-place team needed.
R32_SLOTS = [
    # (match_id, fixed_slot_a, fixed_slot_b_if_no_3rd, eligible_3rd_groups)
    # fixed_slot_a is a (position, group) tuple; third_slot_groups is the eligible set
    {"id": 1,  "fixed": ("1", "E"), "vs_fixed": None,  "eligible_3rd": set("ABCDF")},
    {"id": 2,  "fixed": ("1", "I"), "vs_fixed": None,  "eligible_3rd": set("CDFGH")},
    {"id": 3,  "fixed": ("2", "A"), "vs_fixed": ("2","B"), "eligible_3rd": None},
    {"id": 4,  "fixed": ("1", "F"), "vs_fixed": ("2","C"), "eligible_3rd": None},
    {"id": 5,  "fixed": ("2", "K"), "vs_fixed": ("2","L"), "eligible_3rd": None},
    {"id": 6,  "fixed": ("1", "H"), "vs_fixed": ("2","J"), "eligible_3rd": None},
    {"id": 7,  "fixed": ("1", "D"), "vs_fixed": None,  "eligible_3rd": set("BEFIJ")},
    {"id": 8,  "fixed": ("1", "G"), "vs_fixed": None,  "eligible_3rd": set("AEHIJ")},
    {"id": 9,  "fixed": ("1", "C"), "vs_fixed": ("2","F"), "eligible_3rd": None},
    {"id": 10, "fixed": ("2", "E"), "vs_fixed": ("2","I"), "eligible_3rd": None},
    {"id": 11, "fixed": ("1", "A"), "vs_fixed": None,  "eligible_3rd": set("CEFHI")},
    {"id": 12, "fixed": ("1", "L"), "vs_fixed": None,  "eligible_3rd": set("EHIJK")},
    {"id": 13, "fixed": ("1", "J"), "vs_fixed": ("2","H"), "eligible_3rd": None},
    {"id": 14, "fixed": ("2", "D"), "vs_fixed": ("2","G"), "eligible_3rd": None},
    {"id": 15, "fixed": ("1", "B"), "vs_fixed": None,  "eligible_3rd": set("EFGIJ")},
    {"id": 16, "fixed": ("1", "K"), "vs_fixed": None,  "eligible_3rd": set("DEIJL")},
]

# Bracket tree: pairs of R32 match IDs whose winners meet in R16
R16_PAIRS  = [(0,1),(2,3),(4,5),(6,7),(8,9),(10,11),(12,13),(14,15)]
QF_PAIRS   = [(0,1),(2,3),(4,5),(6,7)]   # indices into R16 results
SF_PAIRS   = [(0,1),(2,3)]               # indices into QF results
FINAL_PAIR = (0, 1)                      # indices into SF results

# Group letter that each 3rd-place R32 slot faces (the 1st-place team of that group)
# String keys to match JSON serialization of r32_slots
R32_SLOT_GROUPS = {
    "1": "E", "2": "I", "7":  "D", "8":  "G",
    "11": "A", "12": "L", "15": "B", "16": "K",
}

# Keep for backwards compat
R32_SLOT_OPPONENTS = {int(k): f"vs 1st Group {v}" for k, v in R32_SLOT_GROUPS.items()}


def assign_third_place(advancing_8: list[dict], group_finishers: dict) -> dict:
    """
    Assign the 8 advancing third-place teams to the 8 third-place slots in R32.
    Each slot has a set of eligible groups; a team from that group fills the slot.

    Uses backtracking to guarantee a valid assignment (greedy fails for ~68% of
    the 495 possible qualifying-group combinations). The full official Annex C
    lookup table (495 entries) was not available, so this solves the CSP directly.

    advancing_8: list of dicts with 'group_letter' and 'team'
    group_finishers: dict group -> {1: team, 2: team, 3: team, 4: team}
    Returns dict: slot_id -> team_name
    """
    third_by_group = {t["group_letter"]: t["team"] for t in advancing_8}
    advancing_letters = set(third_by_group.keys())

    third_slots = [s for s in R32_SLOTS if s["eligible_3rd"] is not None]
    # Order most-constrained first to prune early
    third_slots_ordered = sorted(
        third_slots,
        key=lambda s: len(s["eligible_3rd"] & advancing_letters),
    )
    slot_ids = [s["id"] for s in third_slots_ordered]
    eligibles = [sorted(s["eligible_3rd"] & advancing_letters) for s in third_slots_ordered]

    assignment = {}  # slot_id -> group_letter
    used: set[str] = set()

    def backtrack(idx: int) -> bool:
        if idx == len(slot_ids):
            return True
        sid = slot_ids[idx]
        for g in eligibles[idx]:
            if g not in used:
                assignment[sid] = g
                used.add(g)
                if backtrack(idx + 1):
                    return True
                used.discard(g)
                del assignment[sid]
        return False

    if not backtrack(0):
        raise RuntimeError(
            f"No valid Annex C assignment for advancing groups: {sorted(advancing_letters)}"
        )

    return {sid: third_by_group[g] for sid, g in assignment.items()}


def build_r32_matchups(group_finishers: dict, third_assignments: dict) -> list[tuple[str, str]]:
    """
    Build the list of 16 R32 matchups as (team_a, team_b) tuples, in match order.
    group_finishers: dict {group_letter: {1: team, 2: team, 3: team, 4: team}}
    third_assignments: dict {match_id: third_place_team}
    """
    matchups = []
    for slot in R32_SLOTS:
        pos_a, grp_a = slot["fixed"]
        team_a = group_finishers[grp_a][int(pos_a)]

        if slot["vs_fixed"] is not None:
            pos_b, grp_b = slot["vs_fixed"]
            team_b = group_finishers[grp_b][int(pos_b)]
        else:
            team_b = third_assignments[slot["id"]]

        matchups.append((team_a, team_b))
    return matchups
