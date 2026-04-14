from pydantic import BaseModel, EmailStr
from typing import List, Optional


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
    gender: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    fitness_goal: Optional[str] = None
    dietary_preferences: List[str] = []
    is_premium: bool = False
    onboarding_completed: bool = False
    created_at: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """Body for PUT /api/auth/profile — all fields optional."""
    username: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None       # "low" | "moderate" | "high"
    fitness_goal: Optional[str] = None         # "bulk" | "cut" | "maintain"
    dietary_preferences: Optional[List[str]] = None
    is_premium: Optional[bool] = None
    onboarding_completed: Optional[bool] = None


# ---------------------------------------------------------------------------
# XP / rank state
# Returned wherever the current standing of a user needs to be surfaced.
# ---------------------------------------------------------------------------

class XPStatus(BaseModel):
    """
    A user's current XP and rank standing.

    Fields
    ------
    total_xp        : Lifetime XP accumulated (never goes below 0).
    rank            : Current rank name derived from total_xp
                      (Bronze / Silver / Gold / Platinum / Diamond / Crimson).
    rank_progress   : Progress towards the next rank as a float 0.0–1.0.
                      1.0 means the user is at Crimson (max rank).
    xp_to_next_rank : XP still needed to reach the next rank.
                      None when the user is already at Crimson.
    """

    total_xp: int
    rank: str
    rank_progress: float          # 0.0 – 1.0
    xp_to_next_rank: Optional[int] = None


# ---------------------------------------------------------------------------
# Food scan
# ---------------------------------------------------------------------------

class FoodScanResponse(BaseModel):
    """
    Returned to the client after a food photo is analysed.

    Nutrition fields
    ----------------
    food_name   : Human-readable name identified by Gemini.
    score       : Meal health score 0–100 (macro-based, per-meal metric).
    meal_rank   : Meal-quality label derived from the 0–100 score
                  (same tier names as XP ranks, but based on nutrition
                  bands rather than accumulated XP).
    explanation : Gemini's one-sentence health tip for this food.
    calories    : Estimated kcal per serving.
    protein_g   : Estimated protein in grams.
    carbs_g     : Estimated total carbohydrates in grams.
    fat_g       : Estimated total fat in grams.
    fiber_g     : Estimated dietary fibre in grams.

    XP fields
    ---------
    xp_change   : Signed XP delta for this meal (positive or negative).
                  The caller should apply this to the user's stored total_xp
                  and clamp to ≥ 0 before persisting.
    xp_status   : Full XP / rank standing *after* this meal's XP is applied.
                  None if the current XP state was not available (e.g. the
                  database update failed non-fatally).
    """

    # Nutrition
    food_name: str
    score: int
    meal_rank: str
    explanation: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None

    # ID of the persisted row — returned so the frontend can reference it
    # in subsequent calls (e.g. GET /api/meals/suggestions?scan_id=...)
    scan_id: Optional[str] = None

    # XP
    xp_change: int = 0
    xp_status: Optional[XPStatus] = None


class FoodScanError(BaseModel):
    """Returned when scanning fails (bad image, API failure, etc.)."""

    detail: str


# ---------------------------------------------------------------------------
# Workouts
# ---------------------------------------------------------------------------

class SetLogEntry(BaseModel):
    """A single set within an exercise log entry."""
    set_number: int
    reps: int
    weight_kg: Optional[float] = None     # None for bodyweight exercises
    is_bodyweight: bool = False


class ExerciseLogEntry(BaseModel):
    """All sets for one exercise within a workout log."""
    exercise_id: int
    sets: List[SetLogEntry]


class WorkoutLogRequest(BaseModel):
    """Body for POST /workouts/log."""
    plan_id: Optional[int] = None         # None for ad-hoc workouts
    exercises: List[ExerciseLogEntry]
    notes: Optional[str] = None


class ExerciseCreateRequest(BaseModel):
    """Body for POST /workouts/exercises (create custom exercise)."""
    name: str
    muscle_group: str
    equipment: str
    difficulty: str = "intermediate"


class WorkoutPlanRequest(BaseModel):
    """Body for POST /workouts/plans/generate."""
    goal: str                             # muscle_gain | fat_loss | endurance | strength | general_fitness
    days_per_week: int
    notes: Optional[str] = None


class WorkoutXPResponse(BaseModel):
    """Current workout XP and rank standing."""
    total_xp: int
    rank: str
    rank_progress: float
    xp_to_next_rank: Optional[int] = None
    streak: int


# ---------------------------------------------------------------------------
# Habits
# ---------------------------------------------------------------------------

class HabitCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    frequency: str = "daily"          # "daily" | "weekly"
    target_per_week: int = 7


class HabitUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    target_per_week: Optional[int] = None


class HabitCompleteRequest(BaseModel):
    notes: Optional[str] = None


class HabitResponse(BaseModel):
    """A habit with live streak and today's completion status attached."""
    id: str
    name: str
    description: Optional[str] = None
    frequency: str
    target_per_week: int
    archived: bool
    streak: int
    completed_today: bool
    created_at: str


class HabitXPResponse(BaseModel):
    """Current habit XP and rank standing."""
    total_xp: int
    rank: str
    rank_progress: float
    xp_to_next_rank: Optional[int] = None


class HabitStatsResponse(BaseModel):
    """Aggregate habit statistics for a user."""
    total_habits: int
    active_habits: int
    completions_today: int
    completion_rate_7d: float          # 0.0–1.0
    longest_streak: int
    xp_status: HabitXPResponse


# ---------------------------------------------------------------------------
# Todos
# ---------------------------------------------------------------------------

class TodoCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"           # low | medium | high | urgent
    due_date: Optional[str] = None     # ISO date string "YYYY-MM-DD"


class TodoUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None     # pass "" or null to clear


class TodoXPResponse(BaseModel):
    """Current todo XP and rank standing."""
    total_xp: int
    rank: str
    rank_progress: float
    xp_to_next_rank: Optional[int] = None


# ---------------------------------------------------------------------------
# Profile / Overall score
# ---------------------------------------------------------------------------

class FeatureXPSummary(BaseModel):
    """XP + rank summary for one feature pillar."""
    total_xp: int
    rank: str
    rank_progress: float
    xp_to_next_rank: Optional[int] = None


class ProfileOverviewResponse(BaseModel):
    """All-features XP snapshot plus the combined LifeRanked overall rank."""
    nutrition: FeatureXPSummary
    workouts: FeatureXPSummary
    habits: FeatureXPSummary
    todos: FeatureXPSummary
    overall: FeatureXPSummary


class ActivityWindow(BaseModel):
    """Activity counts for one feature over a time window."""
    nutrition_scans: int
    nutrition_avg_score: Optional[float] = None
    workout_sessions: int
    habit_completions: int
    todos_completed: int


class ProfileHistoryResponse(BaseModel):
    """Activity summary for the last 7 and 30 days."""
    last_7_days: ActivityWindow
    last_30_days: ActivityWindow


# ---------------------------------------------------------------------------
# Food history / summary
# ---------------------------------------------------------------------------

class FoodHistoryResponse(BaseModel):
    """Paginated food scan history."""
    items: list
    total: int
    limit: int
    offset: int
    has_more: bool


class MacroTotals(BaseModel):
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class DailySummaryResponse(BaseModel):
    """Today's meals and aggregate nutrition data."""
    date: str
    meals: list
    meal_count: int
    average_score: Optional[float] = None
    totals: MacroTotals


class FoodStreakResponse(BaseModel):
    """Consecutive days with at least one meal logged."""
    streak: int


# ---------------------------------------------------------------------------
# Recipes & meal suggestions
# ---------------------------------------------------------------------------

class RecipeIngredientResponse(BaseModel):
    id: str
    ingredient_name: str
    quantity: str
    unit: str
    is_optional: bool


class RecipeResponse(BaseModel):
    """Recipe summary (without ingredients)."""
    id: str
    name: str
    cuisine: str
    description: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    prep_time_minutes: Optional[int] = None
    servings: int
    image_url: Optional[str] = None
    is_curated: bool


class RecipeDetailResponse(RecipeResponse):
    """Full recipe including ingredient list."""
    ingredients: List[RecipeIngredientResponse] = []


class MealSuggestionsResponse(BaseModel):
    improvement_tips: List[str]
    suggested_recipes: List[RecipeResponse]


class ShoppingListCreateRequest(BaseModel):
    recipe_id: str
    scan_id: Optional[str] = None
    already_have: List[str] = []      # ingredient names the user owns


class ShoppingListItemUpdateRequest(BaseModel):
    ingredient_name: str
    already_have: bool


class ShoppingListUpdateRequest(BaseModel):
    items: List[ShoppingListItemUpdateRequest]


class ShoppingListItemResponse(BaseModel):
    id: str
    ingredient_name: str
    quantity: str
    unit: str
    already_have: bool
    price_estimate: Optional[float] = None


class ShoppingListResponse(BaseModel):
    id: str
    recipe_id: str
    scan_id: Optional[str] = None
    created_at: str
    items: List[ShoppingListItemResponse] = []


class MealSideResponse(BaseModel):
    """One side of a macro comparison."""
    name: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    cost_per_serving: Optional[float] = None   # future Trolley API


class MealComparisonResponse(BaseModel):
    original_meal: MealSideResponse
    new_meal: MealSideResponse
    improvements: List[str]
