"""
scoring.py — Meal scoring + XP / rank system
=============================================

Two parallel systems live here:

  1. MEAL SCORE (0–100)
     Computed from Gemini's macro data.  Pure nutrition maths — unchanged from
     the original implementation.  Used as input to the XP system.

  2. XP / RANK SYSTEM
     XP accumulates over time.  Rank is determined by total XP, not by any
     single meal.  Deranking is triggered by sustained poor eating (3-day
     average below 40) rather than a single bad scan.

                  ┌──────────┬───────────┐
                  │  Rank    │  Min XP   │
                  ├──────────┼───────────┤
                  │  Bronze  │       0   │
                  │  Silver  │     500   │
                  │  Gold    │   1,500   │
                  │  Platinum│   4,000   │
                  │  Diamond │  10,000   │
                  │  Crimson │  25,000   │
                  └──────────┴───────────┘
"""

from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Rank table
# Ordered lowest → highest.  Both XP thresholds (for the rank system) and
# score bands (kept for backwards-compat / meal-quality labels) live here.
# ---------------------------------------------------------------------------

RANKS: list[dict] = [
    {"name": "Bronze",   "min_xp":     0, "min_score":  0},
    {"name": "Silver",   "min_xp":   500, "min_score": 40},
    {"name": "Gold",     "min_xp": 1_500, "min_score": 55},
    {"name": "Platinum", "min_xp": 4_000, "min_score": 70},
    {"name": "Diamond",  "min_xp":10_000, "min_score": 80},
    {"name": "Crimson",  "min_xp":25_000, "min_score": 90},
]

# Derank threshold: daily average must stay above this or the streak counter
# starts incrementing.
DERANK_DAILY_AVERAGE_THRESHOLD = 40

# Number of consecutive days below the threshold before a derank fires.
DERANK_STREAK_DAYS = 3


# ---------------------------------------------------------------------------
# XP helpers
# ---------------------------------------------------------------------------

def calculate_xp_change(meal_score: int) -> int:
    """
    Return the signed XP change for a single meal.

    Zones
    -----
    ≥ 70  Positive XP.  Grows quadratically — eating great scales up fast.
          +20 XP at score 70, +100 XP at score 100.

    40–69 Small positive XP.  Neutral-to-okay eating keeps progress ticking.
          0 XP at 40, +15 XP at 69.

    < 40  Negative XP.  Junk food hurts — but quadratically, so occasional
          slip-ups sting less than a sustained pattern of bad choices.
          0 XP at 40, −100 XP at score 0.

    XP never goes below 0 (enforced by the caller when updating totals).
    """
    score = max(0, min(100, int(meal_score)))

    if score >= 70:
        # Quadratic from +20 (at 70) to +100 (at 100)
        t = (score - 70) / 30.0
        return round(20 + 80 * t ** 2)

    if score >= 40:
        # Linear from 0 (at 40) to +15 (at 69)
        t = (score - 40) / 30.0
        return round(15 * t)

    # Quadratic penalty from 0 (at 40) to −100 (at 0)
    t = (40 - score) / 40.0
    return -round(100 * t ** 2)


def get_rank_from_xp(total_xp: int) -> str:
    """Return the rank name for a given total XP value."""
    for tier in reversed(RANKS):
        if total_xp >= tier["min_xp"]:
            return tier["name"]
    return RANKS[0]["name"]


def get_rank_progress(total_xp: int) -> float:
    """
    Return progress towards the next rank as a float in [0.0, 1.0].

    Returns 1.0 for Crimson (max rank — no next tier exists).
    """
    total_xp = max(0, total_xp)

    for i, tier in enumerate(RANKS):
        is_last = i == len(RANKS) - 1
        at_this_tier = total_xp >= tier["min_xp"]
        at_next_tier = not is_last and total_xp >= RANKS[i + 1]["min_xp"]

        if at_this_tier and (is_last or not at_next_tier):
            if is_last:
                return 1.0
            current_floor = tier["min_xp"]
            next_floor = RANKS[i + 1]["min_xp"]
            return round((total_xp - current_floor) / (next_floor - current_floor), 4)

    return 0.0


def xp_to_next_rank(total_xp: int) -> Optional[int]:
    """
    Return how many XP are needed to reach the next rank.

    Returns None when the user is already at Crimson (max rank).
    """
    total_xp = max(0, total_xp)
    for i, tier in enumerate(RANKS[:-1]):
        next_tier = RANKS[i + 1]
        if total_xp < next_tier["min_xp"]:
            return next_tier["min_xp"] - total_xp
    return None  # Crimson


def apply_xp_change(current_xp: int, change: int) -> int:
    """Apply a signed XP delta, clamping the result to a minimum of 0."""
    return max(0, current_xp + change)


# ---------------------------------------------------------------------------
# Derank
# ---------------------------------------------------------------------------

def check_derank(user_daily_averages_last_3_days: list[float]) -> bool:
    """
    Return True if the user should derank.

    A derank fires when ALL of the last DERANK_STREAK_DAYS daily average
    scores are strictly below DERANK_DAILY_AVERAGE_THRESHOLD (40).

    Parameters
    ----------
    user_daily_averages_last_3_days
        List of daily average meal scores (floats 0–100), most-recent last.
        Must have at least DERANK_STREAK_DAYS entries to trigger a derank;
        a shorter list (e.g. new user) always returns False.

    Examples
    --------
    >>> check_derank([35.0, 38.0, 39.0])  # all below 40 → derank
    True
    >>> check_derank([35.0, 38.0, 41.0])  # last day OK → no derank
    False
    >>> check_derank([35.0, 38.0])         # only 2 days → no derank
    False
    """
    if len(user_daily_averages_last_3_days) < DERANK_STREAK_DAYS:
        return False
    last_n = user_daily_averages_last_3_days[-DERANK_STREAK_DAYS:]
    return all(avg < DERANK_DAILY_AVERAGE_THRESHOLD for avg in last_n)


def get_derank_xp(current_xp: int) -> int:
    """
    Return the XP value to set when a derank is triggered.

    The user drops to the midpoint of the rank *below* their current one.
    Bronze is the floor — you cannot drop below it (returns 0).

    Midpoints are computed from the RANKS table so they stay in sync
    automatically if thresholds ever change.

    Examples
    --------
    Current rank  → drops to  → lands at
    Silver  (500)    Bronze      0            (floor, no rank below Bronze)
    Gold   (1500)    Silver    250            (midpoint of 0–500)
    Platinum(4000)   Gold     1000            (midpoint of 500–1500)
    Diamond(10000)   Platinum 2750            (midpoint of 1500–4000)
    Crimson(25000)   Diamond  7000            (midpoint of 4000–10000)
    """
    current_rank_index = 0
    for i, tier in enumerate(RANKS):
        if current_xp >= tier["min_xp"]:
            current_rank_index = i

    # Already Bronze — cannot derank further
    if current_rank_index == 0:
        return 0

    below = RANKS[current_rank_index - 1]
    current_floor = RANKS[current_rank_index]["min_xp"]

    # Midpoint between the floor of the rank below and the floor of the
    # rank the user is dropping *from*.
    midpoint = (below["min_xp"] + current_floor) // 2
    return midpoint


# ---------------------------------------------------------------------------
# Meal score (0–100) — macro-based
# ---------------------------------------------------------------------------

def get_rank(score: int) -> str:
    """
    Return a meal-quality label based on the 0–100 meal score.

    This is NOT the same as the user's XP rank — it describes how healthy
    a single meal is, and is stored on each food_scan row.
    Uses the min_score thresholds from RANKS so labels stay in sync.
    """
    for tier in reversed(RANKS):
        if score >= tier["min_score"]:
            return tier["name"]
    return RANKS[0]["name"]


def compute_score(gemini_result: dict) -> Tuple[int, str, str]:
    """
    Derive a health score (0–100) from Gemini's macro data.

    Scoring breakdown (100 pts total):
    ┌──────────────────┬─────┬───────────────────────────────────┐
    │ Factor           │ Max │ What it rewards                   │
    ├──────────────────┼─────┼───────────────────────────────────┤
    │ Protein density  │  35 │ % of calories from protein        │
    │ Fibre density    │  25 │ grams of fibre per 100 kcal       │
    │ Fat ratio        │  20 │ lower fat % of calories           │
    │ Net-carb ratio   │  20 │ lower (carbs − fibre) % of cals   │
    └──────────────────┴─────┴───────────────────────────────────┘

    Returns (meal_score, meal_quality_label, explanation).
    The label uses meal score bands — it is NOT the user's XP-based rank.
    """
    calories   = float(gemini_result.get("calories",  0) or 0)
    protein_g  = float(gemini_result.get("protein_g", 0) or 0)
    carbs_g    = float(gemini_result.get("carbs_g",   0) or 0)
    fat_g      = float(gemini_result.get("fat_g",     0) or 0)
    fiber_g    = float(gemini_result.get("fiber_g",   0) or 0)
    health_tip = gemini_result.get("health_tip", "")

    if calories <= 0:
        score = 50
        return score, get_rank(score), health_tip or "Could not estimate nutritional score."

    # 1. Protein density (0–35 pts)
    protein_pct = (protein_g * 4) / calories
    if protein_pct >= 0.40:   protein_pts = 35
    elif protein_pct >= 0.30: protein_pts = 28
    elif protein_pct >= 0.20: protein_pts = 20
    elif protein_pct >= 0.10: protein_pts = 12
    else:                     protein_pts = 3

    # 2. Fibre density (0–25 pts)
    fiber_per_100kcal = fiber_g / (calories / 100)
    if fiber_per_100kcal >= 3.0:   fiber_pts = 25
    elif fiber_per_100kcal >= 2.0: fiber_pts = 20
    elif fiber_per_100kcal >= 1.0: fiber_pts = 14
    elif fiber_per_100kcal >= 0.5: fiber_pts = 8
    else:                          fiber_pts = 2

    # 3. Fat ratio (0–20 pts)
    fat_pct = (fat_g * 9) / calories
    if fat_pct <= 0.15:   fat_pts = 18
    elif fat_pct <= 0.30: fat_pts = 20
    elif fat_pct <= 0.45: fat_pts = 12
    elif fat_pct <= 0.60: fat_pts = 6
    else:                 fat_pts = 1

    # 4. Net-carb ratio (0–20 pts)
    net_carbs = max(carbs_g - fiber_g, 0)
    net_carb_pct = (net_carbs * 4) / calories
    if net_carb_pct <= 0.15:   net_carb_pts = 20
    elif net_carb_pct <= 0.30: net_carb_pts = 15
    elif net_carb_pct <= 0.50: net_carb_pts = 10
    elif net_carb_pct <= 0.70: net_carb_pts = 5
    else:                      net_carb_pts = 0

    score = max(0, min(100, protein_pts + fiber_pts + fat_pts + net_carb_pts))
    explanation = health_tip if health_tip else f"This food scored {score}/100."
    return score, get_rank(score), explanation
