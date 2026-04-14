from fastapi import APIRouter, UploadFile, File, HTTPException

from models.schemas import FoodScanResponse
from services.gemini import analyse_food_image
from services.scoring import compute_score

router = APIRouter()

ALLOWED_MIME_PREFIXES = ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif")


@router.post("/food/scan", response_model=FoodScanResponse)
async def scan_food(photo: UploadFile = File(...)):
    """
    Accept a food photo and return a health score + rank.

    Full flow:
    1. Validate that the upload is an image.
    2. Read bytes and forward to Gemini for food recognition + macro estimation.
    3. Pass Gemini output to the scoring service to get score (0-100) + rank.
    4. Return a FoodScanResponse with all macro and rank data to the frontend.
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

    # 100 MB hard cap — Gemini inline data limit is ~20 MB but this gives a
    # friendly error before the SDK raises its own.
    if len(image_bytes) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be smaller than 100 MB.")

    # --- Gemini: food recognition + macro estimation ---
    gemini_result = await analyse_food_image(image_bytes, content_type)

    # --- Scoring service: score + rank + explanation ---
    score, rank, explanation = compute_score(gemini_result)

    return FoodScanResponse(
        food_name=gemini_result["food_name"],
        score=score,
        rank=rank,
        explanation=explanation,
        calories=gemini_result["calories"],
        protein_g=gemini_result["protein_g"],
        carbs_g=gemini_result["carbs_g"],
        fat_g=gemini_result["fat_g"],
        fiber_g=gemini_result["fiber_g"],
    )
