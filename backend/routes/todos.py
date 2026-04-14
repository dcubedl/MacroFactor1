"""
To-do list endpoints.

All routes require a valid Bearer token (get_current_user dependency).

Routes
------
GET  /api/todos              — list todos (filterable by completed, priority)
POST /api/todos              — create a todo
PUT  /api/todos/{id}         — update title / description / priority / due_date
DEL  /api/todos/{id}         — permanently delete a todo
POST /api/todos/{id}/complete   — mark done, calculate XP
POST /api/todos/{id}/uncomplete — unmark (undo completion)
GET  /api/todos/xp           — current todo XP and rank
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.schemas import TodoCreateRequest, TodoUpdateRequest, TodoXPResponse
from services.auth import get_current_user
from services.todo_scoring import (
    PRODUCTIVITY_BONUS_XP,
    calculate_todo_xp,
    is_productivity_bonus_day,
)
from services.scoring import (
    get_rank_from_xp,
    get_rank_progress,
    xp_to_next_rank,
)
from database.supabase import (
    get_todos,
    create_todo,
    update_todo,
    delete_todo,
    count_todos_completed_today,
    get_todo_xp,
    upsert_todo_xp,
)

router = APIRouter()

_VALID_PRIORITY = {"low", "medium", "high", "urgent"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _xp_response(total_xp: int) -> TodoXPResponse:
    rank = get_rank_from_xp(total_xp)
    return TodoXPResponse(
        total_xp=total_xp,
        rank=rank,
        rank_progress=get_rank_progress(total_xp),
        xp_to_next_rank=xp_to_next_rank(total_xp),
    )


def _parse_due_date(raw: Optional[str]) -> Optional[str]:
    """
    Validate and normalise a due_date string.

    Accepts "YYYY-MM-DD". Returns None if raw is None or empty.
    Raises HTTP 400 for unparseable values.
    """
    if not raw:
        return None
    try:
        date.fromisoformat(raw)
        return raw
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"due_date must be a date in YYYY-MM-DD format, got: {raw!r}",
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/todos")
async def list_todos(
    completed: Optional[bool] = Query(default=None),
    priority: Optional[str]   = Query(default=None),
    user_id: str = Depends(get_current_user),
):
    """
    List todos for the authenticated user.

    Query params
    ------------
    completed : true | false — filter by completion status (omit for all)
    priority  : low | medium | high | urgent — filter by priority (omit for all)
    """
    if priority is not None and priority not in _VALID_PRIORITY:
        raise HTTPException(
            status_code=400,
            detail=f"priority must be one of: {', '.join(sorted(_VALID_PRIORITY))}.",
        )
    return await get_todos(user_id, completed=completed, priority=priority)


@router.post("/todos", status_code=201)
async def create_new_todo(
    body: TodoCreateRequest,
    user_id: str = Depends(get_current_user),
):
    """Create a new todo for the authenticated user."""
    if body.priority not in _VALID_PRIORITY:
        raise HTTPException(
            status_code=400,
            detail=f"priority must be one of: {', '.join(sorted(_VALID_PRIORITY))}.",
        )

    todo_data: dict = {
        "title":    body.title.strip(),
        "priority": body.priority,
    }
    if body.description is not None:
        todo_data["description"] = body.description
    if body.due_date:
        todo_data["due_date"] = _parse_due_date(body.due_date)

    return await create_todo(user_id, todo_data)


@router.put("/todos/{todo_id}")
async def update_existing_todo(
    todo_id: str,
    body: TodoUpdateRequest,
    user_id: str = Depends(get_current_user),
):
    """Update title, description, priority, or due_date on a todo."""
    updates: dict = {}

    if body.title is not None:
        updates["title"] = body.title.strip()
    if body.description is not None:
        updates["description"] = body.description
    if body.priority is not None:
        if body.priority not in _VALID_PRIORITY:
            raise HTTPException(
                status_code=400,
                detail=f"priority must be one of: {', '.join(sorted(_VALID_PRIORITY))}.",
            )
        updates["priority"] = body.priority
    if body.due_date is not None:
        # Empty string → clear the due date
        updates["due_date"] = _parse_due_date(body.due_date) if body.due_date else None

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    return await update_todo(user_id, todo_id, updates)


@router.delete("/todos/{todo_id}", status_code=204)
async def delete_existing_todo(
    todo_id: str,
    user_id: str = Depends(get_current_user),
):
    """Permanently delete a todo (no soft delete)."""
    await delete_todo(user_id, todo_id)


@router.post("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Mark a todo as completed and award XP.

    XP rules
    --------
    - Base XP by priority: low=5, medium=10, high=20, urgent=30
    - Completed before due date  → 1.5x
    - Completed on the due date  → 1.0x
    - Completed after due date   → 0.5x
    - 5th+ completion in one day → +20 productivity bonus

    Returns:
        todo       — updated todo row
        xp_earned  — XP credited this action
        xp_status  — full XP / rank standing after this completion
    """
    today = date.today()
    now   = datetime.now(timezone.utc).isoformat()

    # Fetch the todo and verify ownership / not already complete
    rows = await get_todos(user_id)
    todo = next((r for r in rows if r["id"] == todo_id), None)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found.")
    if todo["completed"]:
        raise HTTPException(status_code=409, detail="Todo is already completed.")

    # Mark complete
    updated = await update_todo(
        user_id,
        todo_id,
        {"completed": True, "completed_at": now},
    )

    # XP calculation
    raw_due = todo.get("due_date")
    due_date: Optional[date] = date.fromisoformat(raw_due) if raw_due else None

    xp_earned = calculate_todo_xp(
        priority=todo["priority"],
        due_date=due_date,
        completed_at=today,
    )

    # Productivity bonus — count completions *including* this one
    try:
        completions_today = await count_todos_completed_today(user_id, today)
        if is_productivity_bonus_day(completions_today):
            xp_earned += PRODUCTIVITY_BONUS_XP
    except Exception:
        pass  # non-fatal — don't block the completion

    # Update XP (todos never derank — just add)
    xp_row = await get_todo_xp(user_id)
    current_xp  = xp_row["total_xp"] if xp_row else 0
    new_total_xp = current_xp + xp_earned
    rank = get_rank_from_xp(new_total_xp)
    await upsert_todo_xp(user_id, new_total_xp, rank)

    return {
        "todo":       updated,
        "xp_earned":  xp_earned,
        "xp_status":  _xp_response(new_total_xp),
    }


@router.post("/todos/{todo_id}/uncomplete")
async def uncomplete_todo(
    todo_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Mark a previously completed todo as not done.

    XP is not reversed — the user keeps what they earned.
    Returns the updated todo row.
    """
    rows = await get_todos(user_id)
    todo = next((r for r in rows if r["id"] == todo_id), None)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found.")
    if not todo["completed"]:
        raise HTTPException(status_code=409, detail="Todo is not completed.")

    updated = await update_todo(
        user_id,
        todo_id,
        {"completed": False, "completed_at": None},
    )
    return updated


@router.get("/todos/xp", response_model=TodoXPResponse)
async def todo_xp_status(user_id: str = Depends(get_current_user)):
    """Return the user's current todo XP, rank, and progress."""
    xp_row = await get_todo_xp(user_id)
    total_xp = xp_row["total_xp"] if xp_row else 0
    return _xp_response(total_xp)
