import os
# import google.generativeai as genai  # uncomment when implementing

# TODO: initialise the Gemini client once at module load time
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel("gemini-1.5-flash")


async def analyse_food_image(image_bytes: bytes) -> dict:
    """
    Send a food photo to Google Gemini and return a structured result.

    Expected return shape:
    {
        "food_name": str,          # e.g. "Grilled Chicken Caesar Salad"
        "description": str,        # brief natural-language description
        "macros": {                # optional — only if Gemini can infer them
            "calories": int,
            "protein_g": float,
            "carbs_g": float,
            "fat_g": float,
        },
        "ingredients": [str],      # list of visible/likely ingredients
        "health_flags": [str],     # e.g. ["high sodium", "processed", "fried"]
    }

    Implementation notes:
    - Use a multimodal prompt that asks Gemini to identify the food and return
      JSON so we can parse it reliably.
    - Wrap in a try/except and raise HTTPException(502) on Gemini errors so the
      route can surface a clean error to the client.
    - Consider caching identical image hashes to avoid redundant API calls.
    """

    # Placeholder — replace with real Gemini call
    return {
        "food_name": "Placeholder Food",
        "description": "Gemini integration not yet implemented.",
        "macros": None,
        "ingredients": [],
        "health_flags": [],
    }
