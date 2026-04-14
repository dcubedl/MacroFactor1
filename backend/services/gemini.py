import os
import json
import re

import google.generativeai as genai
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Client — lazily initialised on first call so missing env vars surface as
# a clean 500 rather than a crash at import time.
# ---------------------------------------------------------------------------
_model: genai.GenerativeModel | None = None

GEMINI_MODEL = "gemini-2.0-flash"

PROMPT = """You are a professional nutritionist analysing a food photo.

Identify the food and estimate its nutritional values for ONE typical serving.

Respond with ONLY a valid JSON object — no markdown, no code fences, no extra text.
Use exactly these keys:

{
  "food_name": "<specific name, e.g. 'Grilled Chicken Caesar Salad'>",
  "calories": <number>,
  "protein_g": <number>,
  "carbs_g": <number>,
  "fat_g": <number>,
  "fiber_g": <number>,
  "health_tip": "<one actionable tip about this food, max 20 words>"
}

Rules:
- All numeric values must be plain numbers (no units, no strings).
- Base estimates on a standard restaurant or home-cooked single serving.
- If the food is ambiguous, make your best educated guess from what is visible.
- health_tip should be specific to this food, not generic advice.
"""


def _get_model() -> genai.GenerativeModel:
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY environment variable is not set. "
                       "Copy .env.example to .env and add your key.",
            )
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(GEMINI_MODEL)
    return _model


def _parse_json(text: str) -> dict:
    """
    Parse Gemini's text response as JSON.

    Gemini occasionally wraps output in ```json ... ``` fences despite being
    asked not to. Strip them before parsing.
    """
    cleaned = text.strip()
    # Remove opening fence (```json or ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    # Remove closing fence
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned.strip())


def _coerce_number(value, default: float = 0.0) -> float:
    """Safely cast Gemini's value to float, falling back to default."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


async def analyse_food_image(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    """
    Send a food photo to Gemini and return structured nutrition data.

    Parameters
    ----------
    image_bytes  : Raw bytes of the uploaded image.
    content_type : MIME type reported by the client (e.g. "image/jpeg").

    Returns
    -------
    {
        "food_name": str,
        "calories":  float,
        "protein_g": float,
        "carbs_g":   float,
        "fat_g":     float,
        "fiber_g":   float,
        "health_tip": str,
    }

    Raises
    ------
    HTTPException 400 — image bytes are empty.
    HTTPException 502 — Gemini API call failed or returned unparseable output.
    """
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    model = _get_model()

    try:
        response = model.generate_content(
            [
                PROMPT,
                {"mime_type": content_type, "data": image_bytes},
            ]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API request failed: {exc}",
        )

    # Safety check — Gemini can refuse to process certain images
    if not response.text:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned an empty response. "
                   "The image may have been blocked by safety filters.",
        )

    try:
        raw = _parse_json(response.text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse Gemini response as JSON: {exc}. "
                   f"Raw response: {response.text[:300]}",
        )

    return {
        "food_name": str(raw.get("food_name", "Unknown Food")),
        "calories":  _coerce_number(raw.get("calories")),
        "protein_g": _coerce_number(raw.get("protein_g")),
        "carbs_g":   _coerce_number(raw.get("carbs_g")),
        "fat_g":     _coerce_number(raw.get("fat_g")),
        "fiber_g":   _coerce_number(raw.get("fiber_g")),
        "health_tip": str(raw.get("health_tip", "")),
    }
