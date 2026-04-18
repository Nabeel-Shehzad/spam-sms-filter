"""Feedback routes — report misclassified messages."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_optional_user
from backend.api.schemas import FeedbackRequest, FeedbackResponse
from backend.db.crud import create_feedback
from backend.db.database import get_db
from backend.db.models import User

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_optional_user),
):
    fb = await create_feedback(db, log_id=body.log_id, correct_label=body.correct_label)
    return FeedbackResponse(
        id=fb.id,
        log_id=fb.log_id,
        correct_label=fb.correct_label,
        submitted_at=fb.submitted_at,
    )
