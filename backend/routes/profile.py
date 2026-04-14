"""
Profile / overall LifeRanked endpoints.

All routes require a valid Bearer token (get_current_user dependency).

Routes
------
GET /api/profile/overview — all four feature XPs + combined LifeRanked rank
GET /api/profile/history  — activity counts for the last 7 and 30 days
"""

import asyncio
from datetime import date, timedelta

from fastapi import APIRouter, Depends

from models.schemas import (
    ActivityWindow,
    FeatureXPSummary,
    ProfileHistoryResponse,
    ProfileOverviewResponse,
)
from services.auth import get_current_user
from services.overall_score import calculate_overall_xp, feature_rank_summary, overall_rank_summary
from database.supabase import (
    get_nutrition_xp,
    get_workout_xp,
    get_habit_xp,
    get_todo_xp,
    get_nutrition_activity,
    get_workout_activity,
    get_habit_activity,
    get_todo_activity,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_feature_summary(xp_row: dict | None) -> FeatureXPSummary:
    total_xp = xp_row["total_xp"] if xp_row else 0
    summary = feature_rank_summary(total_xp)
    return FeatureXPSummary(**summary)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/profile/overview", response_model=ProfileOverviewResponse)
async def profile_overview(user_id: str = Depends(get_current_user)):
    """
    Return XP and rank for all four features plus the combined LifeRanked rank.

    All four XP tables are queried concurrently.
    """
    n_row, w_row, h_row, t_row = await asyncio.gather(
        get_nutrition_xp(user_id),
        get_workout_xp(user_id),
        get_habit_xp(user_id),
        get_todo_xp(user_id),
    )

    n_xp = n_row["total_xp"] if n_row else 0
    w_xp = w_row["total_xp"] if w_row else 0
    h_xp = h_row["total_xp"] if h_row else 0
    t_xp = t_row["total_xp"] if t_row else 0

    overall_xp = calculate_overall_xp(n_xp, w_xp, h_xp, t_xp)

    return ProfileOverviewResponse(
        nutrition=FeatureXPSummary(**feature_rank_summary(n_xp)),
        workouts=FeatureXPSummary(**feature_rank_summary(w_xp)),
        habits=FeatureXPSummary(**feature_rank_summary(h_xp)),
        todos=FeatureXPSummary(**feature_rank_summary(t_xp)),
        overall=FeatureXPSummary(**overall_rank_summary(overall_xp)),
    )


@router.get("/profile/history", response_model=ProfileHistoryResponse)
async def profile_history(user_id: str = Depends(get_current_user)):
    """
    Return activity summaries for the last 7 and 30 days across all features.

    All eight DB queries run concurrently (four features × two windows).
    """
    today = date.today()
    since_7  = today - timedelta(days=7)
    since_30 = today - timedelta(days=30)

    (
        n7, w7, h7, t7,
        n30, w30, h30, t30,
    ) = await asyncio.gather(
        get_nutrition_activity(user_id, since_7),
        get_workout_activity(user_id, since_7),
        get_habit_activity(user_id, since_7),
        get_todo_activity(user_id, since_7),
        get_nutrition_activity(user_id, since_30),
        get_workout_activity(user_id, since_30),
        get_habit_activity(user_id, since_30),
        get_todo_activity(user_id, since_30),
    )

    return ProfileHistoryResponse(
        last_7_days=ActivityWindow(
            nutrition_scans=n7["scans"],
            nutrition_avg_score=n7["avg_score"],
            workout_sessions=w7["sessions"],
            habit_completions=h7["completions"],
            todos_completed=t7["completed"],
        ),
        last_30_days=ActivityWindow(
            nutrition_scans=n30["scans"],
            nutrition_avg_score=n30["avg_score"],
            workout_sessions=w30["sessions"],
            habit_completions=h30["completions"],
            todos_completed=t30["completed"],
        ),
    )
