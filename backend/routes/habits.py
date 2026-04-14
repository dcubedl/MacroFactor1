"""
Habit tracker endpoints.

All routes require a valid Bearer token (get_current_user dependency).

Routes
------
GET    /api/habits                   — list active habits (streak + today status)
POST   /api/habits                   — create a habit
PUT    /api/habits/{id}              — update name / description / frequency
DELETE /api/habits/{id}              — archive a habit (soft delete)
POST   /api/habits/{id}/complete     — mark habit done for today
DELETE /api/habits/{id}/complete     — undo today's completion
GET    /api/habits/stats             — aggregate stats + XP status
GET    /api/habits/xp                — current habit XP and rank
"""

from datetime import date, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    HabitCreateRequest,
    HabitUpdateRequest,
    HabitCompleteRequest,
    HabitResponse,
    HabitXPResponse,
    HabitStatsResponse,
)
from services.auth import get_current_user
from services.habit_scoring import (
    ALL_HABITS_BONUS_XP,
    DERANK_WINDOW_DAYS,
    STREAK_BREAK_PENALTY_XP,
    calculate_completion_xp,
    calculate_habit_streak,
    check_habit_derank,
    was_streak_broken,
)
from services.scoring import (
    apply_xp_change,
    get_derank_xp,
    get_rank_from_xp,
    get_rank_progress,
    xp_to_next_rank,
)
from database.supabase import (
    get_habits,
    create_habit,
    update_habit,
    archive_habit,
    get_completions_since,
    mark_habit_complete,
    unmark_habit_complete,
    get_habit_xp,
    upsert_habit_xp,
)

router = APIRouter()

_VALID_FREQUENCY = {"daily", "weekly"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _xp_response(total_xp: int) -> HabitXPResponse:
    rank = get_rank_from_xp(total_xp)
    return HabitXPResponse(
        total_xp=total_xp,
        rank=rank,
        rank_progress=get_rank_progress(total_xp),
        xp_to_next_rank=xp_to_next_rank(total_xp),
    )


def _build_habit_responses(
    habits: list[dict],
    completions: list[dict],
    today: date,
) -> list[HabitResponse]:
    """
    Attach streak and completed_today to each habit row.

    completions is the flat list returned by get_completions_since — we
    group by habit_id here so streak calculation is O(n) overall.
    """
    by_habit: dict[str, list[date]] = defaultdict(list)
    today_set: set[str] = set()

    for c in completions:
        hid = c["habit_id"]
        d = date.fromisoformat(c["completed_at"])
        by_habit[hid].append(d)
        if d == today:
            today_set.add(hid)

    result = []
    for h in habits:
        hid = h["id"]
        dates = by_habit.get(hid, [])
        streak = calculate_habit_streak(dates, today)
        result.append(HabitResponse(
            id=hid,
            name=h["name"],
            description=h.get("description"),
            frequency=h["frequency"],
            target_per_week=h["target_per_week"],
            archived=h["archived"],
            streak=streak,
            completed_today=hid in today_set,
            created_at=h["created_at"],
        ))
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/habits", response_model=list[HabitResponse])
async def list_habits(user_id: str = Depends(get_current_user)):
    """Return all active habits with live streak and today's completion status."""
    today = date.today()
    # 32 days of history is enough for the longest streak tier (30+) plus buffer.
    since = today - timedelta(days=32)

    habits, completions = await _fetch_habits_and_completions(user_id, since)
    return _build_habit_responses(habits, completions, today)


async def _fetch_habits_and_completions(
    user_id: str,
    since: date,
) -> tuple[list[dict], list[dict]]:
    """Fetch habits and completions concurrently (two DB calls)."""
    import asyncio
    habits_task = asyncio.create_task(get_habits(user_id))
    completions_task = asyncio.create_task(get_completions_since(user_id, since))
    habits = await habits_task
    completions = await completions_task
    return habits, completions


@router.post("/habits", status_code=201, response_model=HabitResponse)
async def create_new_habit(
    body: HabitCreateRequest,
    user_id: str = Depends(get_current_user),
):
    """Create a new habit for the authenticated user."""
    if body.frequency not in _VALID_FREQUENCY:
        raise HTTPException(
            status_code=400,
            detail=f"frequency must be one of: {', '.join(sorted(_VALID_FREQUENCY))}.",
        )
    if not 1 <= body.target_per_week <= 7:
        raise HTTPException(
            status_code=400,
            detail="target_per_week must be between 1 and 7.",
        )

    habit_data = {
        "name":            body.name.strip(),
        "description":     body.description,
        "frequency":       body.frequency,
        "target_per_week": body.target_per_week,
    }
    row = await create_habit(user_id, habit_data)

    return HabitResponse(
        id=row["id"],
        name=row["name"],
        description=row.get("description"),
        frequency=row["frequency"],
        target_per_week=row["target_per_week"],
        archived=row["archived"],
        streak=0,
        completed_today=False,
        created_at=row["created_at"],
    )


@router.put("/habits/{habit_id}", response_model=HabitResponse)
async def update_existing_habit(
    habit_id: str,
    body: HabitUpdateRequest,
    user_id: str = Depends(get_current_user),
):
    """Update the name, description, or frequency of a habit."""
    updates = {}
    if body.name is not None:
        updates["name"] = body.name.strip()
    if body.description is not None:
        updates["description"] = body.description
    if body.frequency is not None:
        if body.frequency not in _VALID_FREQUENCY:
            raise HTTPException(
                status_code=400,
                detail=f"frequency must be one of: {', '.join(sorted(_VALID_FREQUENCY))}.",
            )
        updates["frequency"] = body.frequency
    if body.target_per_week is not None:
        if not 1 <= body.target_per_week <= 7:
            raise HTTPException(
                status_code=400,
                detail="target_per_week must be between 1 and 7.",
            )
        updates["target_per_week"] = body.target_per_week

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    row = await update_habit(user_id, habit_id, updates)

    today = date.today()
    since = today - timedelta(days=32)
    completions = await get_completions_since(user_id, since)
    by_habit: dict[str, list[date]] = defaultdict(list)
    today_set: set[str] = set()
    for c in completions:
        hid = c["habit_id"]
        d = date.fromisoformat(c["completed_at"])
        by_habit[hid].append(d)
        if d == today:
            today_set.add(hid)

    dates = by_habit.get(habit_id, [])
    streak = calculate_habit_streak(dates, today)

    return HabitResponse(
        id=row["id"],
        name=row["name"],
        description=row.get("description"),
        frequency=row["frequency"],
        target_per_week=row["target_per_week"],
        archived=row["archived"],
        streak=streak,
        completed_today=habit_id in today_set,
        created_at=row["created_at"],
    )


@router.delete("/habits/{habit_id}", status_code=204)
async def archive_existing_habit(
    habit_id: str,
    user_id: str = Depends(get_current_user),
):
    """Soft-delete a habit by archiving it (data is preserved)."""
    await archive_habit(user_id, habit_id)


@router.post("/habits/{habit_id}/complete")
async def complete_habit(
    habit_id: str,
    body: HabitCompleteRequest = HabitCompleteRequest(),
    user_id: str = Depends(get_current_user),
):
    """
    Mark a habit as completed for today.

    Calculates XP with streak multiplier, applies streak-break penalty if
    applicable, checks for all-habits-done bonus, and updates habit_xp.

    Returns:
        xp_earned     — XP credited this action (after all adjustments)
        streak        — New streak length
        xp_status     — Full XP / rank standing after this completion
    """
    today = date.today()
    since = today - timedelta(days=32)

    # Fetch past completions for this habit only (for streak + break detection)
    all_completions = await get_completions_since(user_id, since)
    habit_dates = [
        date.fromisoformat(c["completed_at"])
        for c in all_completions
        if c["habit_id"] == habit_id
    ]

    # Detect streak break (was there a gap before today?)
    broke_streak = was_streak_broken(habit_dates, today)

    # Insert today's completion (raises 409 if already done)
    await mark_habit_complete(user_id, habit_id, today, body.notes)

    # Streak length *after* today's completion
    new_streak = calculate_habit_streak(habit_dates + [today], today)

    # XP for this completion
    xp_earned = calculate_completion_xp(new_streak)

    # Penalty if they broke a streak coming in today
    if broke_streak:
        xp_earned += STREAK_BREAK_PENALTY_XP   # negative, so this reduces xp_earned

    # All-daily-habits-done bonus?
    habits = await get_habits(user_id)
    daily_habits = [h for h in habits if h["frequency"] == "daily"]
    if daily_habits:
        # Re-fetch completions (now includes the one we just inserted)
        fresh_completions = await get_completions_since(user_id, today)
        done_today = {c["habit_id"] for c in fresh_completions if c["completed_at"] == today.isoformat()}
        all_done = all(h["id"] in done_today for h in daily_habits)
        if all_done:
            xp_earned += ALL_HABITS_BONUS_XP

    # Update habit_xp
    xp_row = await get_habit_xp(user_id)
    current_xp = xp_row["total_xp"] if xp_row else 0
    new_total_xp = apply_xp_change(current_xp, xp_earned)

    # Check derank (best-effort)
    try:
        window_start = today - timedelta(days=DERANK_WINDOW_DAYS)
        window_completions = await get_completions_since(user_id, window_start)
        daily_habit_ids = {h["id"] for h in daily_habits}
        completions_in_window = sum(
            1 for c in window_completions
            if c["habit_id"] in daily_habit_ids
        )
        if check_habit_derank(len(daily_habits), completions_in_window):
            derank_target = get_derank_xp(new_total_xp)
            if derank_target is not None:
                new_total_xp = derank_target
    except Exception:
        pass

    new_total_xp = max(0, new_total_xp)
    rank = get_rank_from_xp(new_total_xp)
    await upsert_habit_xp(user_id, new_total_xp, rank)

    return {
        "xp_earned":  xp_earned,
        "streak":     new_streak,
        "xp_status":  _xp_response(new_total_xp),
    }


@router.delete("/habits/{habit_id}/complete", status_code=204)
async def uncomplete_habit(
    habit_id: str,
    user_id: str = Depends(get_current_user),
):
    """Remove today's completion for a habit (undo). Does not reverse XP."""
    today = date.today()
    await unmark_habit_complete(user_id, habit_id, today)


# ---------------------------------------------------------------------------
# Stats & XP
# ---------------------------------------------------------------------------

@router.get("/habits/stats", response_model=HabitStatsResponse)
async def habit_stats(user_id: str = Depends(get_current_user)):
    """
    Return aggregate habit statistics.

    - total_habits / active_habits counts
    - completions today
    - 7-day completion rate (0.0–1.0)
    - longest current streak across all habits
    - current XP status
    """
    today = date.today()
    window_start = today - timedelta(days=DERANK_WINDOW_DAYS)
    since_32 = today - timedelta(days=32)

    habits, completions_32d = await _fetch_habits_and_completions(user_id, since_32)

    active_habits = [h for h in habits if not h["archived"]]
    daily_habits  = [h for h in active_habits if h["frequency"] == "daily"]

    # Group completions by habit
    by_habit: dict[str, list[date]] = defaultdict(list)
    for c in completions_32d:
        by_habit[c["habit_id"]].append(date.fromisoformat(c["completed_at"]))

    # Today's completions
    completions_today = sum(
        1 for dates in by_habit.values()
        if today in dates
    )

    # 7-day completion rate (daily habits only)
    completions_in_window = sum(
        1
        for h in daily_habits
        for d in by_habit.get(h["id"], [])
        if d >= window_start
    )
    max_possible = len(daily_habits) * DERANK_WINDOW_DAYS
    completion_rate = (completions_in_window / max_possible) if max_possible > 0 else 0.0

    # Longest current streak
    longest_streak = 0
    for h in active_habits:
        s = calculate_habit_streak(by_habit.get(h["id"], []), today)
        if s > longest_streak:
            longest_streak = s

    # XP status
    xp_row = await get_habit_xp(user_id)
    total_xp = xp_row["total_xp"] if xp_row else 0

    return HabitStatsResponse(
        total_habits=len(habits),
        active_habits=len(active_habits),
        completions_today=completions_today,
        completion_rate_7d=round(completion_rate, 4),
        longest_streak=longest_streak,
        xp_status=_xp_response(total_xp),
    )


@router.get("/habits/xp", response_model=HabitXPResponse)
async def habit_xp_status(user_id: str = Depends(get_current_user)):
    """Return the user's current habit XP, rank, and progress."""
    xp_row = await get_habit_xp(user_id)
    total_xp = xp_row["total_xp"] if xp_row else 0
    return _xp_response(total_xp)
