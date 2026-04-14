"""
To-do XP scoring service.

Base XP by priority
-------------------
  low    →  5 XP
  medium → 10 XP
  high   → 20 XP
  urgent → 30 XP

Timing modifiers
----------------
  Completed before due date (or no due date) → 1.5x
  Completed on the due date                  → 1.0x  (on time, no bonus)
  Completed after due date                   → 0.5x  (late, half credit)

No due date is treated as "on time" (1.0x — no bonus, no penalty).

Productivity bonus
------------------
  +20 XP flat when the user completes 5 or more todos in a single calendar day.
  Applied at most once per day (the 5th completion triggers it; further
  completions that day do not stack).

No deranking
------------
  Todo XP never decreases.  Rank only climbs.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRIORITY_XP: dict[str, int] = {
    "low":    5,
    "medium": 10,
    "high":   20,
    "urgent": 30,
}

EARLY_MULTIPLIER = 1.5   # before due date
ONTIME_MULTIPLIER = 1.0  # on due date or no due date
LATE_MULTIPLIER = 0.5    # after due date

PRODUCTIVITY_BONUS_XP = 20
PRODUCTIVITY_THRESHOLD = 5   # todos completed in one day to earn the bonus


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def calculate_todo_xp(
    priority: str,
    due_date: Optional[date],
    completed_at: date,
) -> int:
    """
    Return the XP earned for completing a single todo.

    Parameters
    ----------
    priority:
        One of "low", "medium", "high", "urgent".
    due_date:
        The task's due date, or None if no deadline was set.
    completed_at:
        The calendar date on which the todo was marked complete.

    Returns
    -------
    int — XP earned (always ≥ 1).
    """
    base = PRIORITY_XP.get(priority, PRIORITY_XP["medium"])

    if due_date is None:
        multiplier = ONTIME_MULTIPLIER
    elif completed_at < due_date:
        multiplier = EARLY_MULTIPLIER
    elif completed_at == due_date:
        multiplier = ONTIME_MULTIPLIER
    else:
        multiplier = LATE_MULTIPLIER

    return max(1, round(base * multiplier))


def is_productivity_bonus_day(completions_today: int) -> bool:
    """
    Return True if this completion is exactly the 5th one today,
    triggering the productivity bonus.

    Call with the count *after* the new completion is recorded so that
    the bonus fires on the 5th and not again on the 6th, 7th, etc.

    Parameters
    ----------
    completions_today:
        Number of todos completed today (including the current one).
    """
    return completions_today == PRODUCTIVITY_THRESHOLD
