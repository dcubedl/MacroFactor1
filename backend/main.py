from dotenv import load_dotenv

# load_dotenv() must run before any other local imports so that module-level
# code in database/supabase.py and services/gemini.py can read env vars.
load_dotenv()

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.auth import router as auth_router
from routes.food import router as food_router
from routes.workouts import router as workouts_router
from routes.habits import router as habits_router
from routes.todos import router as todos_router
from routes.profile import router as profile_router

logger = logging.getLogger("liferanked")

app = FastAPI(title="LifeRanked API", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS
# Allow requests from the Vite dev server and any future production domain.
# Tighten allow_origins before deploying to production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev port
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global error handler
# Catches any unhandled exception and returns a clean JSON 500 instead of
# leaking a Python stack trace to the client.  The full traceback is logged
# server-side so it is still visible in the terminal / log aggregator.
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    tb = traceback.format_exc()
    logger.error(
        "Unhandled exception on %s %s\n%s",
        request.method,
        request.url.path,
        tb,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router,     prefix="/api")
app.include_router(food_router,     prefix="/api")
app.include_router(workouts_router, prefix="/api")
app.include_router(habits_router,   prefix="/api")
app.include_router(todos_router,    prefix="/api")
app.include_router(profile_router,  prefix="/api")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    """Returns {"status": "ok", "version": "0.1.0"} — useful for uptime checks."""
    return {"status": "ok", "version": "0.1.0"}
