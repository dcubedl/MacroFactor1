from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File

from models.schemas import (
    DailySummaryResponse,
    FoodHistoryResponse,
    FoodScanResponse,
    FoodStreakResponse,
    MacroTotals,
    XPStatus,
)
from services.auth import get_current_user
from services.gemini import analyse_food_image
from services.scoring import (
    apply_xp_change,
    calculate_xp_change,
    compute_score,
    get_rank,
    get_rank_from_xp,
    get_rank_progress,
    xp_to_next_rank,
)
from database.supabase import (
    save_food_scan,
    update_daily_score,
    get_nutrition_xp,
    upsert_nutrition_xp,
    get_food_scans_paginated,
    get_food_scans_for_date,
    get_food_scan_dates,
)

router = APIRouter()

ALLOWED_MIME_PREFIXES = ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif")


@router.post("/food/scan", response_model=FoodScanResponse)
async def scan_food(
    photo: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """
    Accept a food photo and return a health score + rank.

    Requires a valid Bearer token in the Authorization header.

    Full flow:
    1. Validate the upload is an image.
    2. Send to Gemini → food name + macro estimates.
    3. Compute score (0–100) and rank tier.
    4. Persist the scan to Supabase (food_scans table).
    5. Update the user's daily aggregate score.
    6. Return the full result to the frontend.
    """

    # --- Validate content type ---
    content_type = photo.content_type or ""
    if not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{content_type}'. "
                   f"Please upload a JPEG, PNG, WebP, or HEIC image.",
        )

    image_bytes = await photo.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be smaller than 100 MB.")

    # --- Gemini: food recognition + macro estimation ---
    gemini_result = await analyse_food_image(image_bytes, content_type)

    # --- Scoring: meal score (0–100) + meal quality label + explanation ---
    score, meal_rank, explanation = compute_score(gemini_result)
    xp_change = calculate_xp_change(score)

    # --- Persist scan to Supabase ---
    scan_data = {
        "food_name":  gemini_result["food_name"],
        "calories":   gemini_result["calories"],
        "protein_g":  gemini_result["protein_g"],
        "carbs_g":    gemini_result["carbs_g"],
        "fat_g":      gemini_result["fat_g"],
        "fiber_g":    gemini_result["fiber_g"],
        "score":      score,
        "rank":       meal_rank,
        "health_tip": gemini_result["health_tip"],
    }
    saved_scan = await save_food_scan(user_id, scan_data)
    scan_id = saved_scan.get("id") if saved_scan else None

    # --- Update daily aggregate (best-effort — don't fail the scan if it errors) ---
    try:
        today = date.today()
        daily = await update_daily_score(user_id, today, score, meal_rank)
        if daily:
            avg = daily.get("average_score", score)
            _ = get_rank(int(avg))  # available for future daily rank response field
    except Exception:
        pass

    # --- Persist nutrition XP ---
    xp_status = None
    try:
        xp_row = await get_nutrition_xp(user_id)
        current_xp = xp_row["total_xp"] if xp_row else 0
        new_total_xp = apply_xp_change(current_xp, xp_change)
        new_rank = get_rank_from_xp(new_total_xp)
        await upsert_nutrition_xp(user_id, new_total_xp, new_rank)
        xp_status = XPStatus(
            total_xp=new_total_xp,
            rank=new_rank,
            rank_progress=get_rank_progress(new_total_xp),
            xp_to_next_rank=xp_to_next_rank(new_total_xp),
        )
    except Exception:
        pass  # non-fatal — frontend can update optimistically from xp_change

    return FoodScanResponse(
        scan_id=scan_id,
        food_name=gemini_result["food_name"],
        score=score,
        meal_rank=meal_rank,
        explanation=explanation,
        calories=gemini_result["calories"],
        protein_g=gemini_result["protein_g"],
        carbs_g=gemini_result["carbs_g"],
        fat_g=gemini_result["fat_g"],
        fiber_g=gemini_result["fiber_g"],
        xp_change=xp_change,
        xp_status=xp_status,
    )


# ---------------------------------------------------------------------------
# Meal history
# ---------------------------------------------------------------------------

@router.get("/food/history", response_model=FoodHistoryResponse)
async def food_history(
    limit: int  = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0,  ge=0),
    user_id: str = Depends(get_current_user),
):
    """
    Return the user's food scan history with offset-based pagination.

    Query params
    ------------
    limit  : items per page (1–100, default 10)
    offset : number of items to skip (default 0)
    """
    items, total = await get_food_scans_paginated(user_id, limit=limit, offset=offset)
    return FoodHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/food/daily-summary", response_model=DailySummaryResponse)
async def daily_summary(user_id: str = Depends(get_current_user)):
    """
    Return today's meals and aggregate nutrition data.

    Includes: meal list, meal count, average score, and macro totals.
    """
    today = date.today()
    meals = await get_food_scans_for_date(user_id, today)

    avg_score: Optional[float] = None
    totals = MacroTotals()

    if meals:
        scores = [m["score"] for m in meals if m.get("score") is not None]
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)

        def _sum(key: str) -> Optional[float]:
            vals = [m[key] for m in meals if m.get(key) is not None]
            return round(sum(vals), 1) if vals else None

        totals = MacroTotals(
            calories=_sum("calories"),
            protein_g=_sum("protein_g"),
            carbs_g=_sum("carbs_g"),
            fat_g=_sum("fat_g"),
            fiber_g=_sum("fiber_g"),
        )

    return DailySummaryResponse(
        date=today.isoformat(),
        meals=meals,
        meal_count=len(meals),
        average_score=avg_score,
        totals=totals,
    )


@router.get("/food/streak", response_model=FoodStreakResponse)
async def food_streak(user_id: str = Depends(get_current_user)):
    """
    Return the number of consecutive days on which the user logged at least
    one meal, ending today or yesterday.
    """
    all_dates = await get_food_scan_dates(user_id)
    streak = _consecutive_day_streak(all_dates, date.today())
    return FoodStreakResponse(streak=streak)


def _consecutive_day_streak(all_dates: list[date], today: date) -> int:
    """Count consecutive days ending on today (or yesterday) with ≥1 entry."""
    if not all_dates:
        return 0
    unique = sorted(set(all_dates), reverse=True)
    if (today - unique[0]).days > 1:
        return 0
    streak = 1
    for i in range(1, len(unique)):
        if (unique[i - 1] - unique[i]).days == 1:
            streak += 1
        else:
            break
    return streak
