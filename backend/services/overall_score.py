"""
Overall LifeRanked score service.

Combines XP from all four feature pillars into a single weighted score using
the same Bronze → Crimson rank thresholds as the individual features.

Weights
-------
  Nutrition  35 %
  Workouts   30 %
  Habits     20 %
  To-dos     15 %

Formula
-------
  overall_xp = round(
      nutrition_xp * 0.35 +
      workout_xp   * 0.30 +
      habit_xp     * 0.20 +
      todo_xp      * 0.15
  )

The result is then passed through the standard rank lookup so that a user
who is strong in one area but weak in others is ranked appropriately.
"""

from __future__ import annotations

from services.scoring import (
    RANKS,
    get_rank_from_xp,
    get_rank_progress,
    xp_to_next_rank,
)

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "nutrition": 0.35,
    "workouts":  0.30,
    "habits":    0.20,
    "todos":     0.15,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def calculate_overall_xp(
    nutrition_xp: int,
    workout_xp: int,
    habit_xp: int,
    todo_xp: int,
) -> int:
    """
    Return the overall LifeRanked XP from the four feature totals.

    Each feature's XP is weighted and summed; the result is rounded to the
    nearest integer and clamped to ≥ 0.
    """
    raw = (
        nutrition_xp * WEIGHTS["nutrition"]
        + workout_xp * WEIGHTS["workouts"]
        + habit_xp   * WEIGHTS["habits"]
        + todo_xp    * WEIGHTS["todos"]
    )
    return max(0, round(raw))


def overall_rank_summary(overall_xp: int) -> dict:
    """
    Return a compact rank summary dict for the overall score.

    Keys: total_xp, rank, rank_progress, xp_to_next_rank
    """
    return {
        "total_xp":        overall_xp,
        "rank":            get_rank_from_xp(overall_xp),
        "rank_progress":   get_rank_progress(overall_xp),
        "xp_to_next_rank": xp_to_next_rank(overall_xp),
    }


def feature_rank_summary(total_xp: int) -> dict:
    """Same shape as overall_rank_summary, used for each individual feature."""
    return overall_rank_summary(total_xp)
