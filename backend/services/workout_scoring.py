"""
Workout XP scoring service.

XP is split into two components that are summed and then multiplied by a streak
multiplier before being credited to the user.

  total_xp = (volume_xp + consistency_xp) * streak_multiplier

Volume XP
---------
Base value comes from the total weighted volume of the session.  Bodyweight
exercises use a fixed per-rep value since there is no external load.

  weighted_volume = sum(sets * reps * weight_kg)   # for weighted exercises
  bodyweight_reps = sum(sets * reps)               # for bodyweight exercises

  volume_xp_base = weighted_volume / VOLUME_DIVISOR + bodyweight_reps * BODYWEIGHT_REP_VALUE

If the session volume beats the user's personal average by more than 10 % a
comparison bonus of up to 50 % is added:

  improvement_ratio = (volume - avg_volume) / avg_volume   # capped at 1.0
  volume_xp = volume_xp_base * (1 + min(improvement_ratio, 1.0) * 0.5)

Consistency XP
--------------
Flat 15 XP for completing any workout at all.

Streak multiplier
-----------------
Based on consecutive calendar days with at least one workout:

  0–2  consecutive days → 1.0x
  3–6                   → 1.1x
  7–13                  → 1.25x
  14–29                 → 1.5x
  30+                   → 2.0x

Derank
------
Three consecutive rest days (no workout logged) triggers the same derank
check used by the nutrition system.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VOLUME_DIVISOR = 1_000          # 1 000 kg·reps → 1 XP
BODYWEIGHT_REP_VALUE = 0.05     # 1 bodyweight rep → 0.05 XP  (20 reps → 1 XP)
CONSISTENCY_XP = 15             # flat bonus per completed workout
MAX_COMPARISON_BONUS = 0.50     # up to +50 % for beating personal average

_STREAK_TIERS = [
    (30, 2.00),
    (14, 1.50),
    (7,  1.25),
    (3,  1.10),
    (0,  1.00),
]

# Minimum consecutive rest days before a derank check is triggered.
DERANK_REST_DAYS = 3


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def calculate_workout_streak(workout_dates: list[date]) -> int:
    """
    Return the current streak (consecutive calendar days with ≥ 1 workout).

    Parameters
    ----------
    workout_dates:
        All dates on which the user completed a workout, in any order.
        Duplicates are allowed (multiple workouts on one day count as one day).

    Returns
    -------
    int — 0 if no workouts; otherwise the length of the most recent
    consecutive-day streak ending on or before today.
    """
    if not workout_dates:
        return 0

    unique_days = sorted(set(workout_dates), reverse=True)
    today = date.today()

    # The streak only counts if the most recent workout was today or yesterday.
    most_recent = unique_days[0]
    gap = (today - most_recent).days
    if gap > 1:
        return 0

    streak = 1
    for i in range(1, len(unique_days)):
        if (unique_days[i - 1] - unique_days[i]).days == 1:
            streak += 1
        else:
            break

    return streak


def _streak_multiplier(streak: int) -> float:
    for min_days, multiplier in _STREAK_TIERS:
        if streak >= min_days:
            return multiplier
    return 1.0


def check_workout_derank(workout_dates: list[date]) -> bool:
    """
    Return True if the user has had DERANK_REST_DAYS (3) or more consecutive
    rest days ending today.

    Parameters
    ----------
    workout_dates:
        All dates on which the user completed a workout.

    Returns
    -------
    bool — True means a derank check should be performed.
    """
    if not workout_dates:
        # No workouts at all — we cannot penalise; only derank if they had
        # previously accumulated XP.  Caller decides.
        return False

    unique_days = set(workout_dates)
    today = date.today()

    for i in range(1, DERANK_REST_DAYS + 1):
        check = date.fromordinal(today.toordinal() - i)
        if check in unique_days:
            return False  # worked out within the window

    return True


def calculate_workout_xp(
    *,
    weighted_volume: float,         # kg * reps across all weighted sets
    bodyweight_reps: int,           # total reps of bodyweight exercises
    avg_volume: Optional[float],    # user's historical average session volume (kg·reps)
    streak: int,                    # current consecutive-day streak
) -> int:
    """
    Compute the XP earned for a single workout session.

    Parameters
    ----------
    weighted_volume:
        Sum of (sets × reps × weight_kg) across all weighted exercises in this
        session.
    bodyweight_reps:
        Sum of (sets × reps) across all bodyweight exercises in this session.
    avg_volume:
        The user's mean weighted_volume across previous sessions.  Pass None
        or 0 if no history exists (no comparison bonus is applied).
    streak:
        Current consecutive-day workout streak (from calculate_workout_streak).

    Returns
    -------
    int — XP earned, always ≥ 0.
    """
    # --- Volume XP (base) ---
    volume_xp_base = (weighted_volume / VOLUME_DIVISOR) + (bodyweight_reps * BODYWEIGHT_REP_VALUE)

    # --- Comparison bonus ---
    if avg_volume and avg_volume > 0 and weighted_volume > avg_volume * 1.10:
        improvement_ratio = (weighted_volume - avg_volume) / avg_volume
        bonus_factor = 1.0 + min(improvement_ratio, 1.0) * MAX_COMPARISON_BONUS
        volume_xp = volume_xp_base * bonus_factor
    else:
        volume_xp = volume_xp_base

    # --- Consistency XP ---
    consistency_xp = CONSISTENCY_XP

    # --- Streak multiplier ---
    multiplier = _streak_multiplier(streak)

    total = (volume_xp + consistency_xp) * multiplier
    return max(0, round(total))
