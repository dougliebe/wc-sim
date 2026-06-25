# Completed match scorelines: {(team_a, team_b): (goals_a, goals_b)}
# Add results here as matches are played. Team names must match src/groups.py exactly.
# Last updated: June 24, 2026 (through matchday 3 of Groups A-C, matchday 2 of Groups K-L)
RESULTS: dict[tuple[str, str], tuple[int, int]] = {
    # --- Group A ---
    ("Mexico", "South Africa"):     (2, 0),  # Jun 11
    ("Korea Republic", "Czechia"):  (2, 1),  # Jun 11
    ("Czechia", "South Africa"):    (1, 1),  # Jun 18
    ("Mexico", "Korea Republic"):   (1, 0),  # Jun 18
    ("Czechia", "Mexico"):          (0, 3),  # Jun 24
    ("South Africa", "Korea Republic"): (1, 0),  # Jun 24

    # --- Group B ---
    ("Canada", "Bosnia"):           (1, 1),  # Jun 12
    ("Switzerland", "Qatar"):       (1, 1),  # Jun 13
    ("Switzerland", "Bosnia"):      (4, 1),  # Jun 18
    ("Canada", "Qatar"):            (6, 0),  # Jun 18
    ("Switzerland", "Canada"):      (2, 1),  # Jun 24
    ("Bosnia", "Qatar"):            (3, 1),  # Jun 24

    # --- Group C ---
    ("Brazil", "Morocco"):          (1, 1),  # Jun 13
    ("Scotland", "Haiti"):          (1, 0),  # Jun 13
    ("Morocco", "Scotland"):        (1, 0),  # Jun 19
    ("Brazil", "Haiti"):            (3, 0),  # Jun 19
    ("Scotland", "Brazil"):         (0, 3),  # Jun 24
    ("Morocco", "Haiti"):           (4, 2),  # Jun 24

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
    ("Ecuador", "Germany"):         (2, 1),  # Jun 25
    ("Cote d'Ivoire", "Curacao"):   (2, 0),  # Jun 25

    # --- Group F ---
    ("Netherlands", "Japan"):       (2, 2),  # Jun 14
    ("Sweden", "Tunisia"):          (5, 1),  # Jun 14
    ("Netherlands", "Sweden"):      (5, 1),  # Jun 20
    ("Japan", "Tunisia"):           (4, 0),  # Jun 20

    # --- Group G ---
    ("Belgium", "Egypt"):           (1, 1),  # Jun 15
    ("Iran", "New Zealand"):        (2, 2),  # Jun 16
    ("Belgium", "Iran"):            (0, 0),  # Jun 21
    ("Egypt", "New Zealand"):       (3, 1),  # Jun 21

    # --- Group H ---
    ("Spain", "Cabo Verde"):        (0, 0),  # Jun 15
    ("Saudi Arabia", "Uruguay"):    (1, 1),  # Jun 15
    ("Spain", "Saudi Arabia"):      (4, 0),  # Jun 21
    ("Uruguay", "Cabo Verde"):      (2, 2),  # Jun 21

    # --- Group I ---
    ("France", "Senegal"):          (3, 1),  # Jun 16
    ("Norway", "Iraq"):             (4, 1),  # Jun 16
    ("France", "Iraq"):             (3, 0),  # Jun 22
    ("Norway", "Senegal"):          (3, 2),  # Jun 22

    # --- Group J ---
    ("Argentina", "Algeria"):       (3, 0),  # Jun 16
    ("Austria", "Jordan"):          (3, 1),  # Jun 17
    ("Argentina", "Austria"):       (2, 0),  # Jun 22
    ("Jordan", "Algeria"):          (1, 2),  # Jun 22

    # --- Group K ---
    ("Portugal", "Congo DR"):       (1, 1),  # Jun 17
    ("Uzbekistan", "Colombia"):     (1, 1),  # Jun 17
    ("Portugal", "Uzbekistan"):     (5, 0),  # Jun 23
    ("Colombia", "Congo DR"):       (1, 0),  # Jun 23

    # --- Group L ---
    ("England", "Croatia"):         (4, 2),  # Jun 17
    ("Ghana", "Panama"):            (1, 0),  # Jun 17
    ("England", "Ghana"):           (0, 0),  # Jun 23
    ("Panama", "Croatia"):          (0, 1),  # Jun 23
}
