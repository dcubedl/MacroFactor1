from pydantic import BaseModel
from typing import Optional


class FoodScanResponse(BaseModel):
    """
    Returned to the client after a food photo is analysed.

    Fields
    ------
    food_name   : Human-readable name identified by Gemini.
    score       : Integer 0-100 representing the food's healthiness.
    rank        : Tier name matching the frontend RANKS list
                  (Bronze / Silver / Gold / Platinum / Diamond / Crimson).
    explanation : Short justification of the score for display in the UI.
    macros      : Optional macro breakdown if Gemini can extract it.
    """

    food_name: str
    score: int
    rank: str
    explanation: str
    macros: Optional[dict] = None  # e.g. {"calories": 320, "protein": 12, ...}


class FoodScanError(BaseModel):
    """Returned when scanning fails (bad image, Gemini error, etc.)."""

    detail: str
