"""
Workout logger and planner endpoints.

All routes require a valid Bearer token (get_current_user dependency).

Routes
------
GET  /workouts/exercises                  — list exercises (global + user custom)
POST /workouts/exercises                  — create a custom exercise
POST /workouts/plans/generate             — AI-generate a workout plan
GET  /workouts/plans                      — list the user's saved plans
POST /workouts/log                        — log a completed workout
GET  /workouts/history                    — recent workout logs
GET  /workouts/xp                         — user's workout XP + rank
"""

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    ExerciseCreateRequest,
    WorkoutLogRequest,
    WorkoutPlanRequest,
    WorkoutXPResponse,
)
from services.auth import get_current_user, require_premium
from services.workout_scoring import (
    calculate_workout_xp,
    calculate_workout_streak,
    check_workout_derank,
)
from services.scoring import (
    apply_xp_change,
    get_derank_xp,
    get_rank_from_xp,
    get_rank_progress,
    xp_to_next_rank,
)
from services.workout_planner import generate_workout_plan
from database.supabase import (
    get_exercises,
    create_custom_exercise,
    save_workout_plan,
    get_workout_plans,
    save_workout_log,
    get_workout_history,
    get_workout_log_dates,
    get_workout_xp,
    upsert_workout_xp,
)

router = APIRouter()

_VALID_MUSCLE_GROUPS = {
    "chest", "back", "shoulders", "arms", "legs", "core", "cardio", "full_body"
}
_VALID_EQUIPMENT = {
    "barbell", "dumbbell", "machine", "cable", "bodyweight", "kettlebell",
    "resistance_band", "smith_machine", "other"
}
_VALID_DIFFICULTY = {"beginner", "intermediate", "advanced"}


# ---------------------------------------------------------------------------
# Exercises
# ---------------------------------------------------------------------------

@router.get("/workouts/exercises")
async def list_exercises(user_id: str = Depends(get_current_user)):
    """Return all global exercises plus the user's custom exercises."""
    return await get_exercises(user_id)


@router.post("/workouts/exercises", status_code=201)
async def create_exercise(
    body: ExerciseCreateRequest,
    user_id: str = Depends(get_current_user),
):
    """Create a new custom exercise for the authenticated user."""
    if body.muscle_group not in _VALID_MUSCLE_GROUPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid muscle_group '{body.muscle_group}'. "
                   f"Must be one of: {', '.join(sorted(_VALID_MUSCLE_GROUPS))}.",
        )
    if body.equipment not in _VALID_EQUIPMENT:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid equipment '{body.equipment}'. "
                   f"Must be one of: {', '.join(sorted(_VALID_EQUIPMENT))}.",
        )
    if body.difficulty not in _VALID_DIFFICULTY:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid difficulty '{body.difficulty}'. "
                   f"Must be one of: {', '.join(sorted(_VALID_DIFFICULTY))}.",
        )

    exercise_data = {
        "name":         body.name.strip(),
        "muscle_group": body.muscle_group,
        "equipment":    body.equipment,
        "difficulty":   body.difficulty,
    }
    return await create_custom_exercise(user_id, exercise_data)


# ---------------------------------------------------------------------------
# Workout plans
# ---------------------------------------------------------------------------

@router.post("/workouts/plans/generate", status_code=201)
async def generate_plan(
    body: WorkoutPlanRequest,
    user_id: str = Depends(require_premium),   # PREMIUM-ONLY
):
    """
    Generate an AI workout plan via Gemini, then save and return it.

    The plan is personalised to the user's goal and days_per_week.
    """
    exercises = await get_exercises(user_id)
    if not exercises:
        raise HTTPException(
            status_code=503,
            detail="No exercises found in the library. Check that seed data was applied.",
        )

    plan = await generate_workout_plan(
        goal=body.goal,
        days_per_week=body.days_per_week,
        exercises=exercises,
        user_notes=body.notes or "",
    )

    # Attach metadata before persisting
    plan["goal"]         = body.goal
    plan["days_per_week"] = body.days_per_week

    saved = await save_workout_plan(user_id, plan)
    plan["id"] = saved["id"]
    return plan


@router.get("/workouts/plans")
async def list_plans(user_id: str = Depends(get_current_user)):
    """Return all workout plans created by the user, newest first."""
    return await get_workout_plans(user_id)


# ---------------------------------------------------------------------------
# Workout logging
# ---------------------------------------------------------------------------

@router.post("/workouts/log", status_code=201)
async def log_workout(
    body: WorkoutLogRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Log a completed workout session and update the user's workout XP.

    Returns the log row plus the updated XP status.
    """
    if not body.exercises:
        raise HTTPException(status_code=400, detail="exercises list cannot be empty.")

    # Compute volume metrics for XP calculation
    weighted_volume = 0.0
    bodyweight_reps_total = 0

    for ex_entry in body.exercises:
        for s in ex_entry.sets:
            if s.is_bodyweight or s.weight_kg is None:
                bodyweight_reps_total += s.reps
            else:
                weighted_volume += s.reps * s.weight_kg

    # Get historical average volume (best-effort)
    avg_volume = None
    try:
        history = await get_workout_history(user_id, limit=50)
        if history:
            volumes = []
            for log in history:
                vol = 0.0
                for ex in log.get("workout_log_exercises", []):
                    for set_data in (ex.get("sets_completed") or []):
                        w = set_data.get("weight_kg") or 0
                        r = set_data.get("reps") or 0
                        if not set_data.get("is_bodyweight") and w:
                            vol += r * w
                if vol > 0:
                    volumes.append(vol)
            if volumes:
                avg_volume = sum(volumes) / len(volumes)
    except Exception:
        pass

    # Current streak
    streak = 0
    try:
        log_dates = await get_workout_log_dates(user_id)
        streak = calculate_workout_streak(log_dates)
    except Exception:
        pass

    # Calculate XP
    xp_earned = calculate_workout_xp(
        weighted_volume=weighted_volume,
        bodyweight_reps=bodyweight_reps_total,
        avg_volume=avg_volume,
        streak=streak,
    )

    # Save the log
    log_data = {
        "plan_id":   body.plan_id,
        "notes":     body.notes,
        "exercises": [
            {
                "exercise_id": ex.exercise_id,
                "sets": [s.model_dump() for s in ex.sets],
            }
            for ex in body.exercises
        ],
    }
    saved_log = await save_workout_log(user_id, log_data)

    # Fetch & update XP
    xp_row = await get_workout_xp(user_id)
    current_xp = xp_row["total_xp"] if xp_row else 0

    # Check derank (best-effort — do not fail the log if this errors)
    new_total_xp = current_xp + xp_earned
    try:
        all_dates = await get_workout_log_dates(user_id)
        if check_workout_derank(all_dates):
            derank_target = get_derank_xp(new_total_xp)
            if derank_target is not None:
                new_total_xp = derank_target
    except Exception:
        pass

    new_total_xp = max(0, new_total_xp)
    rank = get_rank_from_xp(new_total_xp)

    xp_row_updated = await upsert_workout_xp(user_id, new_total_xp, rank)

    return {
        "log": saved_log,
        "xp_earned": xp_earned,
        "xp_status": {
            "total_xp":        new_total_xp,
            "rank":            rank,
            "rank_progress":   get_rank_progress(new_total_xp),
            "xp_to_next_rank": xp_to_next_rank(new_total_xp),
            "streak":          streak + 1,  # today counts
        },
    }


@router.get("/workouts/history")
async def workout_history(user_id: str = Depends(get_current_user)):
    """Return the user's 20 most recent workout logs."""
    return await get_workout_history(user_id)


# ---------------------------------------------------------------------------
# XP / rank
# ---------------------------------------------------------------------------

@router.get("/workouts/xp", response_model=WorkoutXPResponse)
async def workout_xp(user_id: str = Depends(get_current_user)):
    """Return the user's current workout XP, rank, and streak."""
    xp_row = await get_workout_xp(user_id)
    total_xp = xp_row["total_xp"] if xp_row else 0

    streak = 0
    try:
        log_dates = await get_workout_log_dates(user_id)
        streak = calculate_workout_streak(log_dates)
    except Exception:
        pass

    rank = get_rank_from_xp(total_xp)

    return WorkoutXPResponse(
        total_xp=total_xp,
        rank=rank,
        rank_progress=get_rank_progress(total_xp),
        xp_to_next_rank=xp_to_next_rank(total_xp),
        streak=streak,
    )
