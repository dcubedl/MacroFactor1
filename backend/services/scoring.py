from typing import Tuple

# ---------------------------------------------------------------------------
# Rank tiers — mirrored from frontend/src/data/ranks.js
# ---------------------------------------------------------------------------
RANKS = [
    {"name": "Bronze",   "min": 0},
    {"name": "Silver",   "min": 40},
    {"name": "Gold",     "min": 55},
    {"name": "Platinum", "min": 70},
    {"name": "Diamond",  "min": 80},
    {"name": "Crimson",  "min": 90},
]


def get_rank(score: int) -> str:
    """Return the rank name for a given score (0–100)."""
    for tier in reversed(RANKS):
        if score >= tier["min"]:
            return tier["name"]
    return RANKS[0]["name"]


def compute_score(gemini_result: dict) -> Tuple[int, str, str]:
    """
    Derive a health score (0–100) from Gemini's macro data.

    Scoring breakdown (100 pts total):
    ┌─────────────────────────────────────────────────────────┐
    │ Factor             │ Max │ What it rewards               │
    ├─────────────────────────────────────────────────────────┤
    │ Protein density    │  35 │ % of calories from protein    │
    │ Fibre density      │  25 │ grams of fibre per 100 kcal   │
    │ Fat ratio          │  20 │ lower fat % of calories       │
    │ Net-carb ratio     │  20 │ lower (carbs-fibre) % of cals │
    └─────────────────────────────────────────────────────────┘

    Typical tier benchmarks (approximate):
      Bronze   (<40)  — candy bar, chips, fast food desserts
      Silver  (40–54) — burger, pizza, fried chicken
      Gold    (55–69) — oatmeal, salmon, whole-grain pasta
      Platinum(70–79) — protein shake, lean stir-fry, tempeh
      Diamond (80–89) — chicken salad, lentil soup, broccoli
      Crimson  (90+)  — edamame, very high protein + high fibre meals
    """

    calories  = float(gemini_result.get("calories",  0) or 0)
    protein_g = float(gemini_result.get("protein_g", 0) or 0)
    carbs_g   = float(gemini_result.get("carbs_g",   0) or 0)
    fat_g     = float(gemini_result.get("fat_g",     0) or 0)
    fiber_g   = float(gemini_result.get("fiber_g",   0) or 0)
    health_tip = gemini_result.get("health_tip", "")

    # Gemini couldn't estimate calories — return a neutral mid-range score
    if calories <= 0:
        score = 50
        return score, get_rank(score), health_tip or "Could not estimate nutritional score."

    # ------------------------------------------------------------------
    # 1. Protein density (0–35 pts)
    #    Fraction of total calories supplied by protein (4 kcal/g).
    # ------------------------------------------------------------------
    protein_pct = (protein_g * 4) / calories
    if protein_pct >= 0.40:
        protein_pts = 35
    elif protein_pct >= 0.30:
        protein_pts = 28
    elif protein_pct >= 0.20:
        protein_pts = 20
    elif protein_pct >= 0.10:
        protein_pts = 12
    else:
        protein_pts = 3

    # ------------------------------------------------------------------
    # 2. Fibre density (0–25 pts)
    #    Grams of fibre per 100 kcal — rewards whole, unprocessed foods.
    # ------------------------------------------------------------------
    fiber_per_100kcal = fiber_g / (calories / 100)
    if fiber_per_100kcal >= 3.0:
        fiber_pts = 25
    elif fiber_per_100kcal >= 2.0:
        fiber_pts = 20
    elif fiber_per_100kcal >= 1.0:
        fiber_pts = 14
    elif fiber_per_100kcal >= 0.5:
        fiber_pts = 8
    else:
        fiber_pts = 2

    # ------------------------------------------------------------------
    # 3. Fat ratio (0–20 pts)
    #    Fat as a fraction of total calories (9 kcal/g).
    #    The ideal range (15–30 %) captures lean meats and legumes.
    # ------------------------------------------------------------------
    fat_pct = (fat_g * 9) / calories
    if fat_pct <= 0.15:
        fat_pts = 18   # very low fat (beans, fruit, rice)
    elif fat_pct <= 0.30:
        fat_pts = 20   # ideal (lean meat, legumes)
    elif fat_pct <= 0.45:
        fat_pts = 12   # moderate (salmon, nuts, eggs)
    elif fat_pct <= 0.60:
        fat_pts = 6    # high (cheese, fried food)
    else:
        fat_pts = 1    # very high (butter, cream sauces)

    # ------------------------------------------------------------------
    # 4. Net-carb ratio (0–20 pts)
    #    (Carbs − Fibre) as a fraction of total calories (4 kcal/g).
    #    Fibre is subtracted because it does not raise blood glucose.
    # ------------------------------------------------------------------
    net_carbs = max(carbs_g - fiber_g, 0)
    net_carb_pct = (net_carbs * 4) / calories
    if net_carb_pct <= 0.15:
        net_carb_pts = 20
    elif net_carb_pct <= 0.30:
        net_carb_pts = 15
    elif net_carb_pct <= 0.50:
        net_carb_pts = 10
    elif net_carb_pct <= 0.70:
        net_carb_pts = 5
    else:
        net_carb_pts = 0

    score = protein_pts + fiber_pts + fat_pts + net_carb_pts
    score = max(0, min(100, score))

    explanation = health_tip if health_tip else f"This food scored {score}/100."
    return score, get_rank(score), explanation
