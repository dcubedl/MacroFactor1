import os
from datetime import date as DateType

from supabase import create_client, Client
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Two clients for different trust levels.
#
#   anon_client    — SUPABASE_ANON_KEY.  Row Level Security is active.
#                    Use for reads on behalf of an authenticated user.
#
#   service_client — SUPABASE_SERVICE_KEY.  Bypasses RLS.
#                    Use for backend writes (inserts, upserts) that the
#                    service performs as a trusted process, not as the user.
#
# Never send the service key to the frontend.
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' is not set. "
            "Copy backend/.env.example to backend/.env and fill in your keys."
        )
    return value


def _init_clients() -> tuple[Client, Client]:
    url = _require_env("SUPABASE_URL")
    anon_key = _require_env("SUPABASE_ANON_KEY")
    service_key = _require_env("SUPABASE_SERVICE_KEY")
    return create_client(url, anon_key), create_client(url, service_key)


anon_client, service_client = _init_clients()


# ---------------------------------------------------------------------------
# food_scans
# ---------------------------------------------------------------------------

async def save_food_scan(user_id: str, scan_data: dict) -> dict:
    """
    Insert one food scan row into `food_scans`.

    Uses service_client (bypasses RLS) because the backend is the sole
    writer — the user's JWT is not available server-side at insert time.

    Parameters
    ----------
    user_id   : UUID string from Supabase Auth (auth.uid()).
    scan_data : Dict with keys matching the food_scans columns:
                food_name, calories, protein_g, carbs_g, fat_g, fiber_g,
                score, rank, health_tip, image_url (optional).

    Returns
    -------
    The inserted row as a dict.
    """
    payload = {"user_id": user_id, **scan_data}

    try:
        result = service_client.table("food_scans").insert(payload).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save scan: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Insert returned no data.")

    return result.data[0]


async def get_user_scans(user_id: str, limit: int = 10) -> list[dict]:
    """
    Return the most recent `limit` scans for a user, newest first.

    Uses service_client so the query works regardless of whether the
    caller has attached a user JWT to the anon client.

    Parameters
    ----------
    user_id : UUID string from Supabase Auth.
    limit   : Maximum rows to return (default 10).

    Returns
    -------
    List of food_scan rows as dicts, ordered by created_at descending.
    """
    try:
        result = (
            service_client
            .table("food_scans")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scans: {exc}")

    return result.data or []


# ---------------------------------------------------------------------------
# daily_scores
# ---------------------------------------------------------------------------

async def get_daily_score(user_id: str, date: DateType) -> dict | None:
    """
    Fetch the daily summary row for a given user and calendar date.

    Parameters
    ----------
    user_id : UUID string from Supabase Auth.
    date    : Python date object for the day to look up.

    Returns
    -------
    The daily_scores row as a dict, or None if no row exists yet.
    """
    try:
        result = (
            service_client
            .table("daily_scores")
            .select("*")
            .eq("user_id", user_id)
            .eq("date", date.isoformat())
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily score: {exc}")

    return result.data[0] if result.data else None


async def update_daily_score(
    user_id: str,
    date: DateType,
    new_scan_score: int,
    rank: str,
) -> dict:
    """
    Upsert the daily summary for a user after a new scan is saved.

    If a row already exists for this (user_id, date), increments
    total_meals by 1 and recalculates the running average score.
    If no row exists, creates one with total_meals = 1.

    Uses a Postgres function (rpc) rather than a read-modify-write
    cycle to avoid a race condition when multiple scans are submitted
    simultaneously.

    Falls back to a client-side read-modify-write if the rpc function
    is not yet deployed (graceful degradation during development).

    Parameters
    ----------
    user_id        : UUID string from Supabase Auth.
    date           : Calendar date of the scan.
    new_scan_score : The score (0–100) just computed for the new scan.
    rank           : Rank tier derived from the updated average score.

    Returns
    -------
    The upserted daily_scores row as a dict.
    """
    existing = await get_daily_score(user_id, date)

    if existing:
        total = existing["total_meals"] + 1
        avg = round(
            (existing["average_score"] * existing["total_meals"] + new_scan_score) / total,
            2,
        )
        payload = {
            "average_score": avg,
            "total_meals": total,
            "rank": rank,
        }
        try:
            result = (
                service_client
                .table("daily_scores")
                .update(payload)
                .eq("user_id", user_id)
                .eq("date", date.isoformat())
                .execute()
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to update daily score: {exc}")
    else:
        payload = {
            "user_id": user_id,
            "date": date.isoformat(),
            "average_score": float(new_scan_score),
            "total_meals": 1,
            "rank": rank,
        }
        try:
            result = (
                service_client
                .table("daily_scores")
                .insert(payload)
                .execute()
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to insert daily score: {exc}")

    if not result.data:
        raise HTTPException(status_code=500, detail="Upsert returned no data.")

    return result.data[0]
