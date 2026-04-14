"""
Habit XP scoring service.

XP per completion
-----------------
  xp = round(BASE_COMPLETION_XP * streak_multiplier(streak_after_today))

Streak multipliers
------------------
  Days 1–3   → 1.0x
  Days 4–7   → 1.5x
  Days 8–14  → 2.0x
  Days 15–29 → 3.0x
  Days 30+   → 5.0x

All-daily-habits-done bonus
---------------------------
  +25 XP flat when every active daily habit is completed for the day.

Streak break penalty
--------------------
  If a habit had an active streak going into today but was skipped (gap > 1
  calendar day), the caller applies −15 XP once per broken habit.

Derank
------
  If the user's completion rate across all daily habits falls below 30 % over
  the last 7 calendar days, a derank check is triggered (same tier drop as the
  nutrition and workout systems).
"""

from __future__ import annotations

from datetime import date

BASE_COMPLETION_XP      = 10
ALL_HABITS_BONUS_XP     = 25
STREAK_BREAK_PENALTY_XP = -15
DERANK_THRESHOLD        = 0.30   # < 30 % completion rate triggers derank
DERANK_WINDOW_DAYS      = 7

_STREAK_TIERS: list[tuple[int, float]] = [
    (30, 5.0),
    (15, 3.0),
    (8,  2.0),
    (4,  1.5),
    (1,  1.0),
]


# ---------------------------------------------------------------------------
# Streak helpers
# ---------------------------------------------------------------------------

def streak_multiplier(streak: int) -> float:
    """Return the XP multiplier for a given streak length."""
    for min_days, mult in _STREAK_TIERS:
        if streak >= min_days:
            return mult
    return 1.0


def calculate_habit_streak(completion_dates: list[date], reference_date: date) -> int:
    """
    Return the streak length for a habit, counted backward from reference_date
    (inclusive).

    The streak is the number of consecutive calendar days ending on or
    immediately before reference_date on which the habit was completed.

    Parameters
    ----------
    completion_dates:
        All dates the habit has been completed (any order, duplicates OK).
    reference_date:
        The date to measure *up to* (usually today).

    Returns
    -------
    0  if the habit was not completed on reference_date or the day before, or
       if there are no completions at all.
    N  (≥ 1) otherwise.
    """
    if not completion_dates:
        return 0

    unique = sorted(
        {d for d in completion_dates if d <= reference_date},
        reverse=True,
    )
    if not unique:
        return 0

    # The streak is only live if the most recent completion is today or yesterday.
    if (reference_date - unique[0]).days > 1:
        return 0

    streak = 1
    for i in range(1, len(unique)):
        if (unique[i - 1] - unique[i]).days == 1:
            streak += 1
        else:
            break

    return streak


def was_streak_broken(completion_dates: list[date], today: date) -> bool:
    """
    Return True if the habit had a previous completion but its last completion
    was more than 1 day ago (meaning at least one day was skipped before today).

    Used to decide whether to apply STREAK_BREAK_PENALTY_XP when the user
    comes back and completes the habit after missing one or more days.
    """
    past = [d for d in completion_dates if d < today]
    if not past:
        return False          # no history → no streak to break
    last = max(past)
    return (today - last).days > 1


# ---------------------------------------------------------------------------
# XP calculation
# ---------------------------------------------------------------------------

def calculate_completion_xp(streak_after: int) -> int:
    """
    Return the XP earned for completing a habit today.

    Parameters
    ----------
    streak_after:
        The streak length *after* today's completion is counted.
    """
    return round(BASE_COMPLETION_XP * streak_multiplier(streak_after))


# ---------------------------------------------------------------------------
# Derank check
# ---------------------------------------------------------------------------

def check_habit_derank(
    total_active_daily_habits: int,
    completions_in_window: int,
    window_days: int = DERANK_WINDOW_DAYS,
) -> bool:
    """
    Return True if the user's habit completion rate is below the derank
    threshold and a derank should be triggered.

    Parameters
    ----------
    total_active_daily_habits:
        Number of active daily habits (archived habits excluded).
    completions_in_window:
        Total completions logged across all daily habits in the window period.
    window_days:
        Length of the look-back window in days (default: 7).

    Examples
    --------
    >>> check_habit_derank(3, 5, 7)   # 5 / 21 = 24 % < 30 % → True
    True
    >>> check_habit_derank(3, 7, 7)   # 7 / 21 = 33 % ≥ 30 % → False
    False
    """
    if total_active_daily_habits == 0 or window_days == 0:
        return False
    max_possible = total_active_daily_habits * window_days
    rate = completions_in_window / max_possible
    return rate < DERANK_THRESHOLD
