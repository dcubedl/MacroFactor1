from pydantic import BaseModel
from typing import Optional


class FoodScanResponse(BaseModel):
    """
    Returned to the client after a food photo is analysed.

    Fields
    ------
    food_name   : Human-readable name identified by Gemini.
    score       : Integer 0–100 representing the food's healthiness.
    rank        : Tier name matching the frontend RANKS list
                  (Bronze / Silver / Gold / Platinum / Diamond / Crimson).
    explanation : Gemini's one-sentence health tip for this food.
    calories    : Estimated kcal per serving (may be None if undetectable).
    protein_g   : Estimated protein in grams.
    carbs_g     : Estimated total carbohydrates in grams.
    fat_g       : Estimated total fat in grams.
    fiber_g     : Estimated dietary fibre in grams.
    """

    food_name: str
    score: int
    rank: str
    explanation: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class FoodScanError(BaseModel):
    """Returned when scanning fails (bad image, API failure, etc.)."""

    detail: str
