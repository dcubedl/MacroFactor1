from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.supabase import anon_client, service_client

# HTTPBearer extracts the token from "Authorization: Bearer <token>".
# auto_error=False lets us return a clean 401 instead of FastAPI's default 403.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """
    FastAPI dependency — verifies a Supabase JWT and returns the user's UUID.

    Usage in a route:
        @router.get("/protected")
        async def protected(user_id: str = Depends(get_current_user)):
            ...

    Raises HTTP 401 if:
    - The Authorization header is absent.
    - The token is malformed, expired, or not recognised by Supabase.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        response = anon_client.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not response or not response.user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return str(response.user.id)


async def require_premium(user_id: str = Depends(get_current_user)) -> str:
    """
    FastAPI dependency — verifies the user has an active premium subscription.

    Usage in a route:
        @router.post("/premium-feature")
        async def feature(user_id: str = Depends(require_premium)):
            ...

    Raises HTTP 403 if the user's `is_premium` flag is not True.
    Returns the user_id (same as get_current_user) so it can be used directly.
    """
    result = (
        service_client
        .table("users")
        .select("is_premium")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    row = result.data[0] if result.data else None
    if not row or not row.get("is_premium", False):
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required.",
        )

    return user_id
