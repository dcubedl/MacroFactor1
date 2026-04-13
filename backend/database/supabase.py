import os
# from supabase import create_client, Client  # uncomment when implementing

# TODO: initialise the Supabase client once at module load time
# _url: str = os.getenv("SUPABASE_URL", "")
# _key: str = os.getenv("SUPABASE_KEY", "")
# supabase: Client = create_client(_url, _key)


async def save_scan_result(user_id: str, scan_data: dict) -> dict:
    """
    Persist a food scan result to the Supabase `food_scans` table.

    Expected table schema (to be created in Supabase dashboard or migration):
        id          uuid primary key default gen_random_uuid()
        user_id     text not null
        food_name   text
        score       int
        rank        text
        macros      jsonb
        created_at  timestamptz default now()

    Parameters
    ----------
    user_id   : The authenticated user's ID (from Supabase Auth JWT).
    scan_data : Dict matching the FoodScanResponse schema.

    Returns the inserted row.
    """

    # Placeholder — replace with real Supabase insert
    # return supabase.table("food_scans").insert({
    #     "user_id": user_id,
    #     **scan_data,
    # }).execute()

    return {}


async def get_user_history(user_id: str, limit: int = 20) -> list:
    """
    Fetch a user's recent scan history, ordered by most recent first.

    TODO: add pagination support (offset / cursor) once the table has data.
    """

    # Placeholder
    # return supabase.table("food_scans") \
    #     .select("*") \
    #     .eq("user_id", user_id) \
    #     .order("created_at", desc=True) \
    #     .limit(limit) \
    #     .execute()

    return []
