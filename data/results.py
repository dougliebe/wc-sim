# Completed match scorelines: {(team_a, team_b): (goals_a, goals_b)}
# Add results here as matches are played. Team names must match src/groups.py exactly.
# Last updated: June 21, 2026 (through matchday 2 of Groups A-F, matchday 1 of Groups G-L,
# and matchday 2 of Group H match 1)
RESULTS: dict[tuple[str, str], tuple[int, int]] = {
    # --- Group A ---
    ("Mexico", "South Africa"):     (2, 0),  # Jun 11
    ("Korea Republic", "Czechia"):  (2, 1),  # Jun 11
    ("Czechia", "South Africa"):    (1, 1),  # Jun 18
    ("Mexico", "Korea Republic"):   (1, 0),  # Jun 18

    # --- Group B ---
    ("Canada", "Bosnia"):           (1, 1),  # Jun 12
    ("Switzerland", "Qatar"):       (1, 1),  # Jun 13
    ("Switzerland", "Bosnia"):      (4, 1),  # Jun 18
    ("Canada", "Qatar"):            (6, 0),  # Jun 18

    # --- Group C ---
    ("Brazil", "Morocco"):          (1, 1),  # Jun 13
    ("Scotland", "Haiti"):          (1, 0),  # Jun 13
    ("Morocco", "Scotland"):        (1, 0),  # Jun 19
    ("Brazil", "Haiti"):            (3, 0),  # Jun 19

    # --- Group D ---
    ("United States", "Paraguay"):  (4, 1),  # Jun 12
    ("Australia", "Turkey"):        (2, 0),  # Jun 13
    ("United States", "Australia"): (2, 0),  # Jun 19
    ("Turkey", "Paraguay"):         (0, 1),  # Jun 19

    # --- Group E ---
    ("Germany", "Curacao"):         (7, 1),  # Jun 14
    ("Cote d'Ivoire", "Ecuador"):   (1, 0),  # Jun 14
    ("Germany", "Cote d'Ivoire"):   (2, 1),  # Jun 20
    ("Ecuador", "Curacao"):         (0, 0),  # Jun 20

    # --- Group F ---
    ("Netherlands", "Japan"):       (2, 2),  # Jun 14
    ("Sweden", "Tunisia"):          (5, 1),  # Jun 14
    ("Netherlands", "Sweden"):      (5, 1),  # Jun 20
    ("Japan", "Tunisia"):           (4, 0),  # Jun 20

    # --- Group G (matchday 1 only; matchday 2 on Jun 21 not yet confirmed) ---
    ("Belgium", "Egypt"):           (1, 1),  # Jun 15
    ("Iran", "New Zealand"):        (2, 2),  # Jun 16

    # --- Group H (matchday 1 + Spain vs Saudi Arabia) ---
    ("Spain", "Cabo Verde"):        (0, 0),  # Jun 15
    ("Saudi Arabia", "Uruguay"):    (1, 1),  # Jun 15
    ("Spain", "Saudi Arabia"):      (0, 1),  # Jun 21

    # --- Group I (matchday 1 only; matchday 2 on Jun 22) ---
    ("France", "Senegal"):          (3, 1),  # Jun 16
    ("Norway", "Iraq"):             (4, 1),  # Jun 16

    # --- Group J (matchday 1 only; matchday 2 on Jun 22) ---
    ("Argentina", "Algeria"):       (3, 0),  # Jun 16
    ("Austria", "Jordan"):          (3, 1),  # Jun 17

    # --- Group K (matchday 1 only; matchday 2 on Jun 23) ---
    ("Portugal", "Congo DR"):       (1, 1),  # Jun 17
    ("Uzbekistan", "Colombia"):     (1, 1),  # Jun 17

    # --- Group L (matchday 1 only; matchday 2 on Jun 23) ---
    ("England", "Croatia"):         (4, 2),  # Jun 17
    ("Ghana", "Panama"):            (1, 0),  # Jun 17
}
