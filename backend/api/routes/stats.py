"""Stats and history routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_optional_user
from backend.api.schemas import LogItem, StatsResponse
from backend.db.crud import get_recent_logs, get_stats
from backend.db.database import get_db
from backend.db.models import User

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user_id = current_user.id if current_user else None
    data = await get_stats(db, user_id=user_id)
    return StatsResponse(**data)


@router.get("/history", response_model=list[LogItem])
async def classification_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user_id = current_user.id if current_user else None
    logs = await get_recent_logs(db, user_id=user_id, limit=limit)
    return [LogItem.model_validate(log) for log in logs]
