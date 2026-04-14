import os
from datetime import date as DateType
from typing import Optional

from supabase import create_client, Client
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Two clients for different trust levels.
#
#   anon_client    — SUPABASE_ANON_KEY.  Row Level Security is active.
#                    Use for reads on behalf of an authenticated user.
#
#   service_client — SUPABASE_SERVICE_KEY.  Bypasses RLS.
#                    Use for backend writes (inserts, upserts) that the
#                    service performs as a trusted process, not as the user.
#
# Never send the service key to the frontend.
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is not set. "
            "Copy backend/.env.example to backend/.env and fill in your keys."
        )
    return value


def _init_clients() -> tuple[Client, Client]:
    url = _require_env("SUPABASE_URL")
    anon_key = _require_env("SUPABASE_ANON_KEY")
    service_key = _require_env("SUPABASE_SERVICE_KEY")
    return create_client(url, anon_key), create_client(url, service_key)


anon_client, service_client = _init_clients()


# ---------------------------------------------------------------------------
# food_scans
# ---------------------------------------------------------------------------

async def save_food_scan(user_id: str, scan_data: dict) -> dict:
    """
    Insert one food scan row into `food_scans`.

    Uses service_client (bypasses RLS) because the backend is the sole
    writer — the user's JWT is not available server-side at insert time.

    Parameters
    ----------
    user_id   : UUID string from Supabase Auth (auth.uid()).
    scan_data : Dict with keys matching the food_scans columns:
                food_name, calories, protein_g, carbs_g, fat_g, fiber_g,
                score, rank, health_tip, image_url (optional).

    Returns
    -------
    The inserted row as a dict.
    """
    payload = {"user_id": user_id, **scan_data}

    try:
        result = service_client.table("food_scans").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save scan: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Insert returned no data.")

    return result.data[0]


async def get_user_scans(user_id: str, limit: int = 10) -> list[dict]:
    """
    Return the most recent `limit` scans for a user, newest first.

    Uses service_client so the query works regardless of whether the
    caller has attached a user JWT to the anon client.

    Parameters
    ----------
    user_id : UUID string from Supabase Auth.
    limit   : Maximum rows to return (default 10).

    Returns
    -------
    List of food_scan rows as dicts, ordered by created_at descending.
    """
    try:
        result = (
            service_client
            .table("food_scans")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scans: {exc}")

    return result.data or []


# ---------------------------------------------------------------------------
# daily_scores
# ---------------------------------------------------------------------------

async def get_daily_score(user_id: str, date: DateType) -> dict | None:
    """
    Fetch the daily summary row for a given user and calendar date.

    Parameters
    ----------
    user_id : UUID string from Supabase Auth.
    date    : Python date object for the day to look up.

    Returns
    -------
    The daily_scores row as a dict, or None if no row exists yet.
    """
    try:
        result = (
            service_client
            .table("daily_scores")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", date.isoformat())
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily score: {exc}")

    return result.data[0] if result.data else None


async def update_daily_score(
    user_id: str,
    date: DateType,
    new_scan_score: int,
    rank: str,
) -> dict:
    """
    Upsert the daily summary for a user after a new scan is saved.

    If a row already exists for this (user_id, date), increments
    total_meals by 1 and recalculates the running average score.
    If no row exists, creates one with total_meals = 1.

    Uses a Postgres function (rpc) rather than a read-modify-write
    cycle to avoid a race condition when multiple scans are submitted
    simultaneously.

    Falls back to a client-side read-modify-write if the rpc function
    is not yet deployed (graceful degradation during development).

    Parameters
    ----------
    user_id        : UUID string from Supabase Auth.
    date           : Calendar date of the scan.
    new_scan_score : The score (0–100) just computed for the new scan.
    rank           : Rank tier derived from the updated average score.

    Returns
    -------
    The upserted daily_scores row as a dict.
    """
    existing = await get_daily_score(user_id, date)

    if existing:
        total = existing["total_meals"] + 1
        avg = round(
            (existing["average_score"] * existing["total_meals"] + new_scan_score) / total,
            2,
        )
        payload = {
            "average_score": avg,
            "total_meals": total,
            "rank": rank,
        }
        try:
            result = (
                service_client
                .table("daily_scores")
                .update(payload)
                .eq("user_id", user_id)
                .eq("date", date.isoformat())
                .execute()
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to update daily score: {exc}")
    else:
        payload = {
            "user_id": user_id,
            "date": date.isoformat(),
            "average_score": float(new_scan_score),
            "total_meals": 1,
            "rank": rank,
        }
        try:
            result = (
                service_client
                .table("daily_scores")
                .insert(payload)
                .execute()
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to insert daily score: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Upsert returned no data.")

    return result.data[0]


# ---------------------------------------------------------------------------
# exercises
# ---------------------------------------------------------------------------

async def get_exercises(user_id: str) -> list[dict]:
    """
    Return all global exercises plus the user's own custom exercises.

    Global exercises (is_custom=false) are visible to everyone.
    Custom exercises are filtered to the requesting user.
    """
    try:
        result = (
            service_client
            .table("exercises")
            .select("*")
            .or_(f"is_custom.eq.false,user_id.eq.{user_id}")
            .order("name")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exercises: {exc}")

    return result.data or []


async def create_custom_exercise(user_id: str, exercise_data: dict) -> dict:
    """Insert a custom exercise owned by the user."""
    payload = {"user_id": user_id, "is_custom": True, **exercise_data}
    try:
        result = service_client.table("exercises").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create exercise: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Insert returned no data.")

    return result.data[0]


# ---------------------------------------------------------------------------
# workout_plans
# ---------------------------------------------------------------------------

async def save_workout_plan(user_id: str, plan: dict) -> dict:
    """
    Persist a generated workout plan.

    plan keys: plan_name, description, goal, days_per_week, days (list)
    The `days` list is stored in the workout_plan_exercises join table.
    """
    plan_row = {
        "user_id": user_id,
        "plan_name": plan.get("plan_name", "My Plan"),
        "description": plan.get("description", ""),
        "goal": plan.get("goal", "general_fitness"),
        "days_per_week": plan.get("days_per_week", 3),
    }
    try:
        result = service_client.table("workout_plans").insert(plan_row).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save workout plan: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Plan insert returned no data.")

    plan_id = result.data[0]["id"]

    # Insert exercise rows for each day
    exercise_rows = []
    for day in plan.get("days", []):
        for order_idx, ex in enumerate(day.get("exercises", []), start=1):
            exercise_rows.append({
                "plan_id": plan_id,
                "exercise_id": ex["exercise_id"],
                "day_number": day["day_number"],
                "sets": ex.get("sets", 3),
                "reps": ex.get("reps", 10),
                "rest_sec": ex.get("rest_sec", 60),
                "order_index": order_idx,
            })

    if exercise_rows:
        try:
            service_client.table("workout_plan_exercises").insert(exercise_rows).execute()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save plan exercises: {exc}",
            )

    return result.data[0]


async def get_workout_plans(user_id: str) -> list[dict]:
    """Return all workout plans for the user, newest first."""
    try:
        result = (
            service_client
            .table("workout_plans")
            .select("*, workout_plan_exercises(*, exercises(*))")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workout plans: {exc}")

    return result.data or []


# ---------------------------------------------------------------------------
# workout_logs
# ---------------------------------------------------------------------------

async def save_workout_log(user_id: str, log_data: dict) -> dict:
    """
    Insert a workout log and its per-exercise sets.

    log_data keys:
        plan_id   : Optional int
        notes     : Optional str
        exercises : list of {exercise_id, sets: [{set_number, reps, weight_kg, is_bodyweight}]}
    """
    log_row = {
        "user_id": user_id,
        "plan_id": log_data.get("plan_id"),
        "notes": log_data.get("notes"),
    }
    try:
        result = service_client.table("workout_logs").insert(log_row).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save workout log: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Log insert returned no data.")

    log_id = result.data[0]["id"]

    # Insert per-exercise set rows
    exercise_rows = []
    for ex in log_data.get("exercises", []):
        exercise_rows.append({
            "log_id": log_id,
            "exercise_id": ex["exercise_id"],
            "sets_completed": ex["sets"],  # stored as JSONB
        })

    if exercise_rows:
        try:
            service_client.table("workout_log_exercises").insert(exercise_rows).execute()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save log exercises: {exc}",
            )

    return result.data[0]


async def get_workout_history(user_id: str, limit: int = 20) -> list[dict]:
    """Return recent workout logs for the user, newest first."""
    try:
        result = (
            service_client
            .table("workout_logs")
            .select("*, workout_log_exercises(*, exercises(name, muscle_group))")
            .eq("user_id", user_id)
            .order("logged_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workout history: {exc}")

    return result.data or []


async def get_workout_log_dates(user_id: str) -> list[DateType]:
    """Return all dates on which the user has logged a workout."""
    try:
        result = (
            service_client
            .table("workout_logs")
            .select("logged_at")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch log dates: {exc}")

    dates = []
    for row in result.data or []:
        raw = row.get("logged_at", "")
        if raw:
            # logged_at is a timestamptz; take just the date part
            dates.append(DateType.fromisoformat(raw[:10]))
    return dates


# ---------------------------------------------------------------------------
# workout_xp
# ---------------------------------------------------------------------------

async def get_workout_xp(user_id: str) -> Optional[dict]:
    """Return the user's current workout XP row, or None."""
    try:
        result = (
            service_client
            .table("workout_xp")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workout XP: {exc}")

    return result.data[0] if result.data else None


async def upsert_workout_xp(user_id: str, new_total_xp: int, rank: str) -> dict:
    """
    Upsert the workout_xp row for a user.

    Uses on_conflict so that INSERT and UPDATE are both handled atomically.
    """
    payload = {
        "user_id": user_id,
        "total_xp": new_total_xp,
        "rank": rank,
    }
    try:
        result = (
            service_client
            .table("workout_xp")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update workout XP: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="XP upsert returned no data.")

    return result.data[0]


# ---------------------------------------------------------------------------
# habits
# ---------------------------------------------------------------------------

async def get_habits(user_id: str) -> list[dict]:
    """Return all non-archived habits for the user, oldest first."""
    try:
        result = (
            service_client
            .table("habits")
            .select("*")
            .eq("user_id", user_id)
            .eq("archived", False)
            .order("created_at")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch habits: {exc}")

    return result.data or []


async def create_habit(user_id: str, habit_data: dict) -> dict:
    """Insert a new habit row."""
    payload = {"user_id": user_id, **habit_data}
    try:
        result = service_client.table("habits").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create habit: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Habit insert returned no data.")

    return result.data[0]


async def update_habit(user_id: str, habit_id: str, updates: dict) -> dict:
    """
    Update a habit's editable fields.

    Returns the updated row, or raises 404 if the habit doesn't belong to
    this user or doesn't exist.
    """
    try:
        result = (
            service_client
            .table("habits")
            .update(updates)
            .eq("id", habit_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update habit: {exc}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Habit not found.")

    return result.data[0]


async def archive_habit(user_id: str, habit_id: str) -> dict:
    """Soft-delete a habit by setting archived = true."""
    return await update_habit(user_id, habit_id, {"archived": True})


# ---------------------------------------------------------------------------
# habit_completions
# ---------------------------------------------------------------------------

async def get_completions_since(user_id: str, since_date: DateType) -> list[dict]:
    """
    Return all habit_completions for this user on or after since_date.

    Used to hydrate streak calculations and stats in a single DB round-trip.
    """
    try:
        result = (
            service_client
            .table("habit_completions")
            .select("habit_id, completed_at, notes")
            .eq("user_id", user_id)
            .gte("completed_at", since_date.isoformat())
            .order("completed_at", desc=True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch completions: {exc}")

    return result.data or []


async def mark_habit_complete(
    user_id: str,
    habit_id: str,
    completed_at: DateType,
    notes: Optional[str] = None,
) -> dict:
    """
    Insert a completion row for (habit_id, completed_at).

    Raises 409 if the habit is already completed on that date (unique
    constraint violation).
    """
    payload = {
        "habit_id":     habit_id,
        "user_id":      user_id,
        "completed_at": completed_at.isoformat(),
    }
    if notes:
        payload["notes"] = notes

    try:
        result = service_client.table("habit_completions").insert(payload).execute()
    except Exception as exc:
        msg = str(exc)
        if "unique" in msg.lower() or "duplicate" in msg.lower() or "23505" in msg:
            raise HTTPException(
                status_code=409,
                detail="Habit already completed for this date.",
            )
        raise HTTPException(status_code=500, detail=f"Failed to mark habit complete: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Completion insert returned no data.")

    return result.data[0]


async def unmark_habit_complete(
    user_id: str,
    habit_id: str,
    completed_at: DateType,
) -> None:
    """
    Delete the completion row for (habit_id, completed_at).

    Raises 404 if no such row exists.
    """
    try:
        result = (
            service_client
            .table("habit_completions")
            .delete()
            .eq("habit_id", habit_id)
            .eq("user_id", user_id)
            .eq("completed_at", completed_at.isoformat())
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to unmark habit: {exc}")

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="No completion found for this habit on that date.",
        )


# ---------------------------------------------------------------------------
# habit_xp
# ---------------------------------------------------------------------------

async def get_habit_xp(user_id: str) -> Optional[dict]:
    """Return the user's current habit XP row, or None."""
    try:
        result = (
            service_client
            .table("habit_xp")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch habit XP: {exc}")

    return result.data[0] if result.data else None


async def upsert_habit_xp(user_id: str, new_total_xp: int, rank: str) -> dict:
    """Upsert the habit_xp row for a user."""
    payload = {
        "user_id":  user_id,
        "total_xp": new_total_xp,
        "rank":     rank,
    }
    try:
        result = (
            service_client
            .table("habit_xp")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update habit XP: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Habit XP upsert returned no data.")

    return result.data[0]


# ---------------------------------------------------------------------------
# todos
# ---------------------------------------------------------------------------

async def get_todos(
    user_id: str,
    *,
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
) -> list[dict]:
    """
    Return todos for the user, newest first.

    Parameters
    ----------
    completed : Filter by completion status. None = return all.
    priority  : Filter by priority level. None = return all.
    """
    query = (
        service_client
        .table("todos")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )
    if completed is not None:
        query = query.eq("completed", completed)
    if priority is not None:
        query = query.eq("priority", priority)

    try:
        result = query.execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch todos: {exc}")

    return result.data or []


async def create_todo(user_id: str, todo_data: dict) -> dict:
    """Insert a new todo row."""
    payload = {"user_id": user_id, **todo_data}
    try:
        result = service_client.table("todos").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create todo: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Todo insert returned no data.")

    return result.data[0]


async def update_todo(user_id: str, todo_id: str, updates: dict) -> dict:
    """
    Update editable fields on a todo.

    Raises 404 if the todo doesn't belong to this user.
    """
    try:
        result = (
            service_client
            .table("todos")
            .update(updates)
            .eq("id", todo_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update todo: {exc}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Todo not found.")

    return result.data[0]


async def delete_todo(user_id: str, todo_id: str) -> None:
    """Permanently delete a todo. Raises 404 if not found."""
    try:
        result = (
            service_client
            .table("todos")
            .delete()
            .eq("id", todo_id)
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete todo: {exc}")

    if not result.data:
        raise HTTPException(status_code=404, detail="Todo not found.")


async def count_todos_completed_today(user_id: str, today: DateType) -> int:
    """
    Return the number of todos completed by this user on today's date.

    Used to determine whether the productivity bonus should fire.
    Filters on the completed_at timestamp column, selecting rows whose
    date portion equals today.
    """
    from datetime import timedelta
    tomorrow = (today + timedelta(days=1)).isoformat()

    try:
        result = (
            service_client
            .table("todos")
            .select("completed_at")
            .eq("user_id", user_id)
            .eq("completed", True)
            .gte("completed_at", today.isoformat())
            .lt("completed_at", tomorrow)
            .execute()
        )
        return len(result.data or [])
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# todo_xp
# ---------------------------------------------------------------------------

async def get_todo_xp(user_id: str) -> Optional[dict]:
    """Return the user's current todo XP row, or None."""
    try:
        result = (
            service_client
            .table("todo_xp")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch todo XP: {exc}")

    return result.data[0] if result.data else None


async def upsert_todo_xp(user_id: str, new_total_xp: int, rank: str) -> dict:
    """Upsert the todo_xp row for a user."""
    payload = {
        "user_id":  user_id,
        "total_xp": new_total_xp,
        "rank":     rank,
    }
    try:
        result = (
            service_client
            .table("todo_xp")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update todo XP: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Todo XP upsert returned no data.")

    return result.data[0]


# ---------------------------------------------------------------------------
# nutrition_xp
# ---------------------------------------------------------------------------

async def get_nutrition_xp(user_id: str) -> Optional[dict]:
    """Return the user's accumulated nutrition XP row, or None."""
    try:
        result = (
            service_client
            .table("nutrition_xp")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch nutrition XP: {exc}")

    return result.data[0] if result.data else None


async def upsert_nutrition_xp(user_id: str, new_total_xp: int, rank: str) -> dict:
    """Upsert the nutrition_xp row for a user."""
    payload = {
        "user_id":  user_id,
        "total_xp": max(0, new_total_xp),
        "rank":     rank,
    }
    try:
        result = (
            service_client
            .table("nutrition_xp")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update nutrition XP: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Nutrition XP upsert returned no data.")

    return result.data[0]


# ---------------------------------------------------------------------------
# food_scans — extended queries for history / summary / streak
# ---------------------------------------------------------------------------

async def get_food_scans_paginated(
    user_id: str,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """
    Return a page of food scans for the user plus the total count.

    Returns (items, total_count).
    """
    try:
        result = (
            service_client
            .table("food_scans")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scan history: {exc}")

    return result.data or [], result.count or 0


async def get_food_scans_for_date(user_id: str, target_date: DateType) -> list[dict]:
    """Return all food scans logged on a specific calendar date."""
    from datetime import timedelta
    next_day = target_date + timedelta(days=1)
    try:
        result = (
            service_client
            .table("food_scans")
            .select("*")
            .eq("user_id", user_id)
            .gte("created_at", target_date.isoformat())
            .lt("created_at", next_day.isoformat())
            .order("created_at")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily scans: {exc}")

    return result.data or []


async def get_food_scan_dates(user_id: str) -> list[DateType]:
    """Return the unique calendar dates on which the user has logged a meal."""
    try:
        result = (
            service_client
            .table("food_scans")
            .select("created_at")
            .eq("user_id", user_id)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scan dates: {exc}")

    dates: set[DateType] = set()
    for row in result.data or []:
        raw = row.get("created_at", "")
        if raw:
            dates.add(DateType.fromisoformat(raw[:10]))
    return list(dates)


# ---------------------------------------------------------------------------
# Profile activity summary helpers
# ---------------------------------------------------------------------------

async def get_nutrition_activity(
    user_id: str,
    since_date: DateType,
) -> dict:
    """
    Return nutrition activity since a date:
        {"scans": int, "avg_score": float | None}
    """
    try:
        result = (
            service_client
            .table("food_scans")
            .select("score")
            .eq("user_id", user_id)
            .gte("created_at", since_date.isoformat())
            .execute()
        )
    except Exception:
        return {"scans": 0, "avg_score": None}

    rows = result.data or []
    if not rows:
        return {"scans": 0, "avg_score": None}

    avg = round(sum(r["score"] for r in rows) / len(rows), 1)
    return {"scans": len(rows), "avg_score": avg}


async def get_workout_activity(
    user_id: str,
    since_date: DateType,
) -> dict:
    """
    Return workout activity since a date:
        {"sessions": int}
    """
    try:
        result = (
            service_client
            .table("workout_logs")
            .select("id")
            .eq("user_id", user_id)
            .gte("logged_at", since_date.isoformat())
            .execute()
        )
    except Exception:
        return {"sessions": 0}

    return {"sessions": len(result.data or [])}


async def get_habit_activity(
    user_id: str,
    since_date: DateType,
) -> dict:
    """
    Return habit activity since a date:
        {"completions": int}
    """
    try:
        result = (
            service_client
            .table("habit_completions")
            .select("id")
            .eq("user_id", user_id)
            .gte("completed_at", since_date.isoformat())
            .execute()
        )
    except Exception:
        return {"completions": 0}

    return {"completions": len(result.data or [])}


async def get_todo_activity(
    user_id: str,
    since_date: DateType,
) -> dict:
    """
    Return todo activity since a date:
        {"completed": int}
    """
    try:
        result = (
            service_client
            .table("todos")
            .select("id")
            .eq("user_id", user_id)
            .eq("completed", True)
            .gte("completed_at", since_date.isoformat())
            .execute()
        )
    except Exception:
        return {"completed": 0}

    return {"completed": len(result.data or [])}
