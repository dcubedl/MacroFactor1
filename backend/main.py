from dotenv import load_dotenv

# load_dotenv() must run before any other local imports so that module-level
# code in database/supabase.py and services/gemini.py can read env vars.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.food import router as food_router
from routes.workouts import router as workouts_router
from routes.habits import router as habits_router

app = FastAPI(title="MacroFactor API", version="0.1.0")

# Allow requests from the Vite dev server and any future production domain.
# Tighten allow_origins before deploying to production.
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

app.include_router(auth_router, prefix="/api")
app.include_router(food_router, prefix="/api")
app.include_router(workouts_router, prefix="/api")
app.include_router(habits_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
