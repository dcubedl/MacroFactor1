from fastapi import APIRouter, UploadFile, File, HTTPException

from models.schemas import FoodScanResponse
from services.gemini import analyse_food_image
from services.scoring import compute_score

router = APIRouter()


@router.post("/food/scan", response_model=FoodScanResponse)
async def scan_food(photo: UploadFile = File(...)):
    """
    Accept a food photo and return a health score + rank.

    Flow (to be implemented):
    1. Read the uploaded image bytes.
    2. Pass bytes to services/gemini.py → get food name, description, macro hints.
    3. Pass Gemini output to services/scoring.py → get integer score 0-100.
    4. Determine rank tier from score.
    5. Optionally persist result to Supabase via database/supabase.py.
    6. Return FoodScanResponse to the client.
    """

    # TODO: validate that the upload is actually an image
    image_bytes = await photo.read()

    # TODO: call Gemini for food recognition
    gemini_result = await analyse_food_image(image_bytes)

    # TODO: derive score from Gemini output
    score, rank, explanation = compute_score(gemini_result)

    return FoodScanResponse(
        food_name=gemini_result.get("food_name", "Unknown"),
        score=score,
        rank=rank,
        explanation=explanation,
        macros=gemini_result.get("macros"),
    )
