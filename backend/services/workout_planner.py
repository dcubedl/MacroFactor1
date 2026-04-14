"""
Gemini-powered workout plan generator.

Builds a prompt from the user's goal, available days per week, and the full
exercise library, then parses the structured JSON plan Gemini returns.
"""

from __future__ import annotations

import json
import re

from fastapi import HTTPException

from services.gemini import _get_model   # reuse the lazy-init Gemini model


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_GOALS = {"muscle_gain", "fat_loss", "endurance", "strength", "general_fitness"}
_VALID_DAYS  = range(1, 8)   # 1–7 days per week

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_json(text: str) -> str:
    """Remove Markdown code fences if Gemini wraps the JSON in them."""
    m = _JSON_FENCE.search(text)
    return m.group(1).strip() if m else text.strip()


def _exercise_library_text(exercises: list[dict]) -> str:
    """Format the exercise library into a compact text block for the prompt."""
    lines = []
    for ex in exercises:
        lines.append(
            f"- {ex['name']} (id={ex['id']}, muscle={ex['muscle_group']}, "
            f"equipment={ex['equipment']}, difficulty={ex['difficulty']})"
        )
    return "\n".join(lines) if lines else "(no exercises available)"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_workout_plan(
    *,
    goal: str,
    days_per_week: int,
    exercises: list[dict],
    user_notes: str = "",
) -> dict:
    """
    Call Gemini to generate a weekly workout plan.

    Parameters
    ----------
    goal          : One of _VALID_GOALS.
    days_per_week : Number of training days per week (1–7).
    exercises     : List of exercise dicts from the database
                    (keys: id, name, muscle_group, equipment, difficulty).
    user_notes    : Optional free-text context from the user (e.g. injuries,
                    preferences).

    Returns
    -------
    dict with keys:
        plan_name   : str
        description : str
        days        : list of day objects, each with:
            day_number    : int (1 = Monday, 7 = Sunday)
            focus         : str (e.g. "Chest & Triceps")
            exercises     : list of:
                exercise_id : int (references exercises table)
                sets        : int
                reps        : int  (target reps per set)
                rest_sec    : int  (seconds between sets)

    Raises
    ------
    HTTPException 400 if goal/days are invalid.
    HTTPException 502 if Gemini fails or returns unparseable output.
    """
    if goal not in _VALID_GOALS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid goal '{goal}'. Must be one of: {', '.join(sorted(_VALID_GOALS))}.",
        )
    if days_per_week not in _VALID_DAYS:
        raise HTTPException(
            status_code=400,
            detail="days_per_week must be between 1 and 7.",
        )

    library_text = _exercise_library_text(exercises)
    notes_section = f"\nUser notes: {user_notes.strip()}" if user_notes.strip() else ""

    prompt = f"""You are an expert personal trainer. Create a {days_per_week}-day-per-week
workout plan for someone whose primary goal is: {goal}.{notes_section}

Return ONLY a JSON object — no markdown, no commentary, no code fences.

JSON schema (all fields required):
{{
  "plan_name": "<short catchy name>",
  "description": "<2–3 sentence summary of the plan and who it suits>",
  "days": [
    {{
      "day_number": <1–7, where 1=Monday>,
      "focus": "<muscle group or theme, e.g. 'Push (Chest/Shoulder/Triceps)'>",
      "exercises": [
        {{
          "exercise_id": <integer id from the library below>,
          "sets": <integer, 1–6>,
          "reps": <integer, 1–30>,
          "rest_sec": <integer, 30–300>
        }}
      ]
    }}
  ]
}}

Rules:
- Include exactly {days_per_week} day objects (one per training day).
- Each day must have 4–8 exercises.
- Only use exercise_ids from the library below — do NOT invent IDs.
- Distribute muscle groups sensibly; avoid training the same muscle on
  consecutive days unless the goal requires it (e.g. full-body for endurance).
- For 'fat_loss' or 'endurance' goals include at least one cardio exercise per day.
- For 'strength' or 'muscle_gain' use compound lifts early in each day.
- Sets/reps/rest should match the goal:
    muscle_gain   → 3–5 sets, 8–12 reps, 60–90 s rest
    fat_loss      → 3–4 sets, 12–15 reps, 30–60 s rest
    endurance     → 2–4 sets, 15–20 reps, 30–45 s rest
    strength      → 4–6 sets,  3–6 reps, 120–300 s rest
    general_fitness → 3 sets, 10–12 reps, 60 s rest

Exercise library:
{library_text}
"""

    model = _get_model()
    try:
        response = await model.generate_content_async(prompt)
        raw = response.text or ""
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini request failed: {exc}",
        ) from exc

    try:
        plan = json.loads(_strip_json(raw))
    except json.JSONDecodeError as exc:
        excerpt = raw[:300]
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse Gemini plan response: {exc}. Raw excerpt: {excerpt!r}",
        ) from exc

    # Basic structure validation
    if "days" not in plan or not isinstance(plan["days"], list):
        raise HTTPException(
            status_code=502,
            detail="Gemini returned a plan without a 'days' list.",
        )

    return plan
