"""
Meal improvement and recipe suggestion service.

Three public functions:

  generate_improvement_tips(scan_result)
      Calls Gemini to produce 3–5 specific, actionable tips for improving the
      scanned meal (e.g. "Swap white rice for brown rice to triple the fibre").

  suggest_recipes(scan_result, available_recipes, n=5)
      Scores each curated recipe using the same macro-based formula as the
      food scanner, filters those that beat the scan's score, and returns the
      top N sorted best-first.  Falls back to Gemini if fewer than 3 curated
      matches are found.

  generate_comparison(original, new_recipe)
      Pure-Python comparison — returns a list of human-readable improvement
      strings such as "2× the protein" or "40% less fat".
"""

from __future__ import annotations

import json
import re
from typing import Optional

from fastapi import HTTPException

from services.gemini import _get_model, _parse_json
from services.scoring import compute_score

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

# Cuisines the suggestions engine knows about
_CUISINES = frozenset({
    "indian", "arab", "japanese", "italian",
    "mexican", "chinese", "british", "korean",
})

# Keyword → cuisine mapping for auto-detection
_CUISINE_KEYWORDS: dict[str, list[str]] = {
    "indian":   ["curry", "dal", "tikka", "biryani", "naan", "samosa",
                 "paneer", "masala", "chutney", "tandoori", "dosa", "idli"],
    "arab":     ["hummus", "shawarma", "falafel", "tabbouleh", "fattoush",
                 "kebab", "pita", "baba ganoush", "mezze", "kofta", "foul"],
    "japanese": ["sushi", "ramen", "miso", "teriyaki", "tempura", "udon",
                 "soba", "edamame", "onigiri", "bento", "yakitori", "tonkatsu"],
    "italian":  ["pasta", "pizza", "risotto", "lasagna", "gnocchi",
                 "carbonara", "pesto", "bruschetta", "caprese", "frittata"],
    "mexican":  ["taco", "burrito", "guacamole", "salsa", "quesadilla",
                 "enchilada", "pozole", "tamale", "fajita", "chimichanga"],
    "chinese":  ["dim sum", "dumpling", "fried rice", "noodle", "wontons",
                 "kung pao", "mapo", "congee", "lo mein", "char siu"],
    "british":  ["shepherd's pie", "fish and chips", "full english",
                 "bangers", "cottage pie", "crumpet", "scone", "pasty"],
    "korean":   ["bibimbap", "kimchi", "bulgogi", "tteokbokki", "japchae",
                 "doenjang", "galbi", "samgyeopsal", "sundubu", "dakgalbi"],
}


# ---------------------------------------------------------------------------
# Cuisine inference
# ---------------------------------------------------------------------------

def infer_cuisine(food_name: str) -> Optional[str]:
    """Return the most likely cuisine from a food name, or None."""
    name_lower = food_name.lower()
    for cuisine, keywords in _CUISINE_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return cuisine
    return None


# ---------------------------------------------------------------------------
# Improvement tips (Gemini)
# ---------------------------------------------------------------------------

async def generate_improvement_tips(scan_result: dict) -> list[str]:
    """
    Ask Gemini for 3–5 specific, actionable improvement tips for the meal.

    Parameters
    ----------
    scan_result : dict with keys food_name, score, calories, protein_g,
                  carbs_g, fat_g, fiber_g.

    Returns
    -------
    List of tip strings.  Falls back to a generic list on any failure so the
    route never 502s just because of tips.
    """
    food_name = scan_result.get("food_name", "Unknown meal")
    score     = scan_result.get("score", 50)
    calories  = scan_result.get("calories") or 0
    protein   = scan_result.get("protein_g") or 0
    carbs     = scan_result.get("carbs_g") or 0
    fat       = scan_result.get("fat_g") or 0
    fiber     = scan_result.get("fiber_g") or 0

    prompt = f"""You are a nutritionist giving advice about a specific meal.

Meal: {food_name}
Health score: {score}/100
Macros per serving: {calories:.0f} kcal | {protein:.1f}g protein | {carbs:.1f}g carbs | {fat:.1f}g fat | {fiber:.1f}g fibre

Generate exactly 3–5 specific, actionable improvement tips for this exact meal.
Each tip should name the food and the specific change, and quantify the benefit where possible.

Good examples:
- "Replace white rice with brown rice to triple the fibre content"
- "Add a handful of spinach to boost iron and folate with only 20 extra calories"
- "Swap the cream sauce for Greek yogurt to cut fat by 60% and double the protein"

Return ONLY a JSON array of strings — no markdown, no code fences, no extra text.
"""

    try:
        model = _get_model()
        response = await model.generate_content_async(prompt)
        raw = response.text or ""
        tips = json.loads(_parse_json(raw) if isinstance(_parse_json(raw), str) else raw)
        # _parse_json returns a dict, so handle the array case
        if isinstance(tips, list):
            return [str(t) for t in tips[:5]]
        raise ValueError("Expected a list")
    except Exception:
        pass

    # Fallback: re-try with a more lenient parse
    try:
        model = _get_model()
        response = await model.generate_content_async(prompt)
        raw = response.text or ""
        # Strip fences manually
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        tips = json.loads(cleaned)
        if isinstance(tips, list):
            return [str(t) for t in tips[:5]]
    except Exception:
        pass

    # Hard fallback — generic tips based on macros
    tips = []
    if fiber < 5:
        tips.append(f"Add vegetables or legumes to {food_name} to boost fibre intake")
    if protein < 20:
        tips.append(f"Add a lean protein source to {food_name} to increase satiety")
    if fat > 20:
        tips.append(f"Reduce oil or choose a leaner cooking method for {food_name}")
    if not tips:
        tips.append(f"Try pairing {food_name} with a side salad to increase micronutrients")
    return tips[:5]


# ---------------------------------------------------------------------------
# Recipe scoring and suggestion
# ---------------------------------------------------------------------------

def _score_recipe(recipe: dict) -> int:
    """Compute the macro-based health score for a recipe dict."""
    score, _, _ = compute_score(recipe)
    return score


async def suggest_recipes(
    scan_result: dict,
    available_recipes: list[dict],
    n: int = 5,
) -> list[dict]:
    """
    Return up to `n` recipes that score higher than the scanned meal.

    Parameters
    ----------
    scan_result       : Scan row dict (food_name, score, calories, macros).
    available_recipes : Recipes fetched from the DB (may be cuisine-filtered).
    n                 : Maximum recipes to return.

    Curated recipes that beat the scan score are ranked best-first.
    If fewer than 3 are found, Gemini generates additional suggestions to
    make up the shortfall.  Gemini-generated recipes are marked
    ``is_curated=False`` and have no ``id``.
    """
    scan_score = scan_result.get("score", 0)
    food_name  = scan_result.get("food_name", "the scanned meal")

    # Score and filter curated recipes
    scored: list[tuple[int, dict]] = []
    for recipe in available_recipes:
        r_score = _score_recipe(recipe)
        if r_score > scan_score:
            scored.append((r_score, recipe))

    scored.sort(key=lambda x: x[0], reverse=True)
    good_recipes = [r for _, r in scored[:n]]

    if len(good_recipes) >= 3:
        return good_recipes

    # --- Gemini fallback -------------------------------------------------------
    need = n - len(good_recipes)
    cuisine = infer_cuisine(food_name)
    cuisine_hint = f" in {cuisine} cuisine" if cuisine else ""

    prompt = f"""You are a nutritionist suggesting healthier meal alternatives.

Original meal: {food_name}
Original macros: {scan_result.get('calories', 0):.0f} kcal | \
{scan_result.get('protein_g', 0):.1f}g protein | \
{scan_result.get('carbs_g', 0):.1f}g carbs | \
{scan_result.get('fat_g', 0):.1f}g fat | \
{scan_result.get('fiber_g', 0):.1f}g fibre
Original health score: {scan_score}/100

Suggest {need} healthier recipe alternatives{cuisine_hint} with noticeably better \
nutritional profiles (higher protein, more fibre, or lower fat).

Return ONLY a JSON array — no markdown, no code fences. Each element must have:
{{
  "name": "<recipe name>",
  "cuisine": "<one of: indian, arab, japanese, italian, mexican, chinese, british, korean>",
  "description": "<1 sentence description>",
  "calories": <number>,
  "protein_g": <number>,
  "carbs_g": <number>,
  "fat_g": <number>,
  "fiber_g": <number>,
  "prep_time_minutes": <integer>,
  "servings": 1,
  "is_curated": false
}}
"""

    try:
        model = _get_model()
        response = await model.generate_content_async(prompt)
        raw = response.text or ""
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        generated = json.loads(cleaned)
        if isinstance(generated, list):
            good_recipes.extend(generated[:need])
    except Exception:
        pass  # Return whatever curated recipes we have

    return good_recipes[:n]


# ---------------------------------------------------------------------------
# Side-by-side comparison (pure Python)
# ---------------------------------------------------------------------------

def generate_comparison(original: dict, new_recipe: dict) -> list[str]:
    """
    Produce human-readable improvement strings comparing two sets of macros.

    Parameters
    ----------
    original   : Dict with nutrition keys (calories, protein_g, etc.)
    new_recipe : Same shape.

    Returns
    -------
    List of strings such as "2× the protein", "40% less fat",
    "300 fewer calories".  Empty list if no meaningful differences.
    """
    comparisons: list[str] = []

    def _fmt_ratio(label: str, orig: float, new: float,
                   higher_is_better: bool = True) -> Optional[str]:
        if orig <= 0:
            return None
        ratio = new / orig
        better = (ratio > 1) if higher_is_better else (ratio < 1)

        if ratio >= 1.9:
            return f"{ratio:.0f}× the {label}"
        if ratio >= 1.25 and higher_is_better:
            return f"{round((ratio - 1) * 100)}% more {label}"
        if ratio <= 0.55 and not higher_is_better:
            return f"{round((1 - ratio) * 100)}% less {label}"
        if ratio <= 0.55 and higher_is_better:
            return f"{round((1 - ratio) * 100)}% less {label}"
        if ratio >= 1.25 and not higher_is_better:
            return f"{round((ratio - 1) * 100)}% more {label}"
        return None

    def _get(d: dict, key: str) -> float:
        return float(d.get(key) or 0)

    # Calories (lower is better for weight management)
    orig_cal = _get(original, "calories")
    new_cal  = _get(new_recipe, "calories")
    if orig_cal > 0:
        cal_diff = orig_cal - new_cal
        if cal_diff >= 100:
            comparisons.append(f"{round(cal_diff)} fewer calories")
        elif new_cal - orig_cal >= 100:
            comparisons.append(f"{round(new_cal - orig_cal)} more calories")

    # Protein (higher is better)
    tip = _fmt_ratio("protein",
                     _get(original, "protein_g"),
                     _get(new_recipe, "protein_g"),
                     higher_is_better=True)
    if tip:
        comparisons.append(tip)

    # Fibre (higher is better)
    tip = _fmt_ratio("fibre",
                     _get(original, "fiber_g"),
                     _get(new_recipe, "fiber_g"),
                     higher_is_better=True)
    if tip:
        comparisons.append(tip)

    # Fat (lower is better)
    orig_fat = _get(original, "fat_g")
    new_fat  = _get(new_recipe, "fat_g")
    if orig_fat > 0 and new_fat < orig_fat * 0.75:
        comparisons.append(f"{round((1 - new_fat / orig_fat) * 100)}% less fat")
    elif orig_fat > 0 and new_fat > orig_fat * 1.5:
        comparisons.append(f"{round((new_fat / orig_fat - 1) * 100)}% more fat")

    # Carbs (contextual — just note large swings)
    orig_carbs = _get(original, "carbs_g")
    new_carbs  = _get(new_recipe, "carbs_g")
    if orig_carbs > 0 and new_carbs < orig_carbs * 0.5:
        comparisons.append(f"{round((1 - new_carbs / orig_carbs) * 100)}% fewer carbs")

    return comparisons or ["Similar nutritional profile with different ingredients"]
