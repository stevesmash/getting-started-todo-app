"""Activity timeline endpoints."""

from typing import List
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas import ActivityLog
from app.storage import store

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/", response_model=List[ActivityLog])
def list_activity(
    limit: int = 50,
    user: str = Depends(get_current_user)
):
    return store.list_activity_logs(user, limit)
