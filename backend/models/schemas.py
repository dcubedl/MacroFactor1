from pydantic import BaseModel, EmailStr
from typing import Optional


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    # True when Supabase email confirmation is enabled and the user must
    # verify their address before the token becomes usable.
    requires_confirmation: bool = False


class UserProfile(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Food scan
# ---------------------------------------------------------------------------

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
