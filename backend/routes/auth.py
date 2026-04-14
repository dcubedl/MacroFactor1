from fastapi import APIRouter, Depends, HTTPException

from models.schemas import AuthResponse, LoginRequest, ProfileUpdateRequest, SignupRequest, UserProfile
from services.auth import get_current_user
from database.supabase import anon_client, service_client

router = APIRouter()


def _auth_error(exc: Exception) -> HTTPException:
    """
    Convert a Supabase / GoTrue exception into a FastAPI HTTPException.
    GoTrue wraps its errors in an object with a .message attribute; fall back
    to str(exc) for anything unexpected.
    """
    message = getattr(exc, "message", None) or str(exc)
    return HTTPException(status_code=400, detail=message)


# ---------------------------------------------------------------------------
# POST /api/auth/signup
# ---------------------------------------------------------------------------

@router.post("/auth/signup", response_model=AuthResponse, status_code=201)
async def signup(body: SignupRequest):
    """
    Create a new account with email + password.

    Flow:
    1. Call Supabase Auth to create the auth.users row.
    2. Insert a matching row in public.users (via service client, since the
       new user has no token yet).
    3. Return the access token if a session was issued immediately, or signal
       that email confirmation is required.
    """
    try:
        auth_resp = anon_client.auth.sign_up(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:
        raise _auth_error(exc)

    user = auth_resp.user
    if not user:
        # Supabase returns a user object even when confirmation is pending,
        # so a missing user means a hard failure.
        raise HTTPException(status_code=400, detail="Signup failed. Please try again.")

    # Insert the public profile row. Use service_client because the user has
    # no JWT yet and RLS would block an anon insert.
    try:
        service_client.table("users").insert(
            {
                "id": user.id,
                "email": user.email,
                "username": body.username,
            }
        ).execute()
    except Exception:
        # The auth user was created. A profile insert failure is non-fatal —
        # the user can still log in and the row can be created on first login.
        # Log this in production (e.g. Sentry) so it doesn't go unnoticed.
        pass

    session = auth_resp.session
    requires_confirmation = session is None

    return AuthResponse(
        access_token=session.access_token if session else "",
        user_id=str(user.id),
        email=user.email or body.email,
        requires_confirmation=requires_confirmation,
    )


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

@router.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """
    Sign in with email + password and return an access token.
    """
    try:
        auth_resp = anon_client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:
        raise _auth_error(exc)

    session = auth_resp.session
    user = auth_resp.user

    if not session or not user:
        raise HTTPException(status_code=401, detail="Login failed. Check your credentials.")

    # Ensure the public.users row exists (covers the edge case where the
    # profile insert failed during signup).
    existing = service_client.table("users").select("id").eq("id", user.id).execute()
    if not existing.data:
        try:
            service_client.table("users").insert(
                {"id": user.id, "email": user.email}
            ).execute()
        except Exception:
            pass

    return AuthResponse(
        access_token=session.access_token,
        user_id=str(user.id),
        email=user.email or "",
    )


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------

@router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    """
    Soft logout — confirms the token is valid, then instructs the client to
    discard it.

    Supabase JWTs are stateless; true server-side invalidation requires
    revoking the refresh token via the Supabase Admin API or enabling the
    'JWT expiry' setting. For now the client is responsible for deleting
    the token from storage.
    """
    return {"message": "Logged out. Please delete your access token client-side."}


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

@router.get("/auth/me", response_model=UserProfile)
async def me(user_id: str = Depends(get_current_user)):
    """
    Return the authenticated user's public profile.
    """
    result = (
        service_client
        .table("users")
        .select("id, email, username, created_at")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="User profile not found.")

    row = result.data[0]
    return UserProfile(
        id=row["id"],
        email=row["email"],
        username=row.get("username"),
        gender=row.get("gender"),
        age=row.get("age"),
        height_cm=row.get("height_cm"),
        weight_kg=row.get("weight_kg"),
        activity_level=row.get("activity_level"),
        fitness_goal=row.get("fitness_goal"),
        dietary_preferences=row.get("dietary_preferences") or [],
        is_premium=row.get("is_premium", False),
        onboarding_completed=row.get("onboarding_completed", False),
        created_at=row.get("created_at"),
    )


# ---------------------------------------------------------------------------
# PUT /api/auth/profile
# ---------------------------------------------------------------------------

@router.put("/auth/profile", response_model=UserProfile)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Update the authenticated user's profile fields.

    All body fields are optional — only provided (non-None) fields are written.
    Typically called immediately after signup to persist onboarding answers.
    Setting any profile field automatically marks onboarding_completed = true
    unless the caller explicitly sets it to false.
    """
    # Build the update payload from non-None fields only
    updates: dict = {}
    if body.username is not None:
        updates["username"] = body.username
    if body.gender is not None:
        updates["gender"] = body.gender
    if body.age is not None:
        updates["age"] = body.age
    if body.height_cm is not None:
        updates["height_cm"] = body.height_cm
    if body.weight_kg is not None:
        updates["weight_kg"] = body.weight_kg
    if body.activity_level is not None:
        updates["activity_level"] = body.activity_level
    if body.fitness_goal is not None:
        updates["fitness_goal"] = body.fitness_goal
    if body.dietary_preferences is not None:
        updates["dietary_preferences"] = body.dietary_preferences
    if body.is_premium is not None:
        updates["is_premium"] = body.is_premium
    if body.onboarding_completed is not None:
        updates["onboarding_completed"] = body.onboarding_completed
    elif updates:
        # Any profile data being set implies onboarding was completed
        updates["onboarding_completed"] = True

    if not updates:
        # Nothing to update — just return current profile
        result = (
            service_client
            .table("users")
            .select("id, email, username, gender, age, height_cm, weight_kg, "
                    "activity_level, fitness_goal, dietary_preferences, "
                    "is_premium, onboarding_completed, created_at")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="User profile not found.")
        row = result.data[0]
    else:
        result = (
            service_client
            .table("users")
            .update(updates)
            .eq("id", user_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="User profile not found.")
        row = result.data[0]

    return UserProfile(
        id=row["id"],
        email=row["email"],
        username=row.get("username"),
        gender=row.get("gender"),
        age=row.get("age"),
        height_cm=row.get("height_cm"),
        weight_kg=row.get("weight_kg"),
        activity_level=row.get("activity_level"),
        fitness_goal=row.get("fitness_goal"),
        dietary_preferences=row.get("dietary_preferences") or [],
        is_premium=row.get("is_premium", False),
        onboarding_completed=row.get("onboarding_completed", False),
        created_at=row.get("created_at"),
    )
