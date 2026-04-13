from typing import Tuple

# ---------------------------------------------------------------------------
# Rank tiers — mirrored from frontend/src/data/ranks.js
# Each tier is (name, min_score_inclusive).
# The list is ordered lowest → highest so we can walk it in reverse to find
# the highest matching tier for a given score.
# ---------------------------------------------------------------------------
RANKS = [
    {"name": "Bronze",   "min": 0},
    {"name": "Silver",   "min": 40},
    {"name": "Gold",     "min": 55},
    {"name": "Platinum", "min": 70},
    {"name": "Diamond",  "min": 80},
    {"name": "Crimson",  "min": 90},
]


def get_rank(score: int) -> str:
    """Return the rank name for a given score (0-100)."""
    for tier in reversed(RANKS):
        if score >= tier["min"]:
            return tier["name"]
    return RANKS[0]["name"]


def compute_score(gemini_result: dict) -> Tuple[int, str, str]:
    """
    Derive a health score (0-100) from Gemini's food analysis.

    Parameters
    ----------
    gemini_result : dict
        Output from services/gemini.analyse_food_image — contains food_name,
        description, macros, ingredients, and health_flags.

    Returns
    -------
    (score, rank_name, explanation)

    Scoring logic (TODO — implement each factor):
    - Start from a neutral baseline (e.g. 60).
    - Penalise for health_flags like "fried", "processed", "high sodium", etc.
    - Reward for flags like "whole grain", "leafy greens", "lean protein", etc.
    - Adjust based on macro ratios when available (e.g. favour protein-dense,
      low-sugar foods).
    - Clamp final score to [0, 100].

    The explanation should be a single sentence surfaced in the UI to help the
    user understand why their food received that score.
    """

    # Placeholder — returns a fixed mid-range score until logic is implemented
    placeholder_score = 50
    rank = get_rank(placeholder_score)
    explanation = "Scoring logic not yet implemented."

    return placeholder_score, rank, explanation
