from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.supabase import anon_client

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
