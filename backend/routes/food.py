from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from models.schemas import FoodScanResponse
from services.auth import get_current_user
from services.gemini import analyse_food_image
from services.scoring import calculate_xp_change, compute_score, get_rank
from database.supabase import save_food_scan, update_daily_score

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
    await save_food_scan(user_id, scan_data)

    # --- Update daily aggregate (best-effort — don't fail the scan if it errors) ---
    try:
        today = date.today()
        daily = await update_daily_score(user_id, today, score, meal_rank)
        if daily:
            avg = daily.get("average_score", score)
            _ = get_rank(int(avg))  # available for future daily rank response field
    except Exception:
        pass

    # xp_status is populated here once the XP persistence layer is wired up.
    # For now, xp_change is returned so the frontend can optimistically update.
    return FoodScanResponse(
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
    )
