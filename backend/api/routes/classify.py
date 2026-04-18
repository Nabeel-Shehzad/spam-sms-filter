"""Classification routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_optional_user
from backend.api.schemas import (
    BatchClassifyItem,
    BatchClassifyRequest,
    BatchClassifyResponse,
    ClassifyRequest,
    ClassifyResponse,
)
from backend.db.crud import create_log
from backend.db.database import get_db
from backend.db.models import User
from backend.ml.predictor import classify, classify_batch
from backend.nlp.language import detect_language

router = APIRouter(prefix="/classify", tags=["classify"])


@router.post("", response_model=ClassifyResponse)
async def classify_single(
    body: ClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    lang = detect_language(body.text)
    result = classify(body.text)
    log = await create_log(
        db,
        message_text=body.text,
        predicted_label=result["label"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        language=lang,
        user_id=current_user.id if current_user else None,
    )
    return ClassifyResponse(
        label=result["label"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        language=lang,
        log_id=log.id,
    )


@router.post("/batch", response_model=BatchClassifyResponse)
async def classify_batch_endpoint(
    body: BatchClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    results = classify_batch(body.texts)
    items = []
    for text, res in zip(body.texts, results):
        lang = detect_language(text)
        log = await create_log(
            db,
            message_text=text,
            predicted_label=res["label"],
            confidence=res["confidence"],
            model_used=res["model_used"],
            language=lang,
            user_id=current_user.id if current_user else None,
        )
        items.append(BatchClassifyItem(
            text=text,
            label=res["label"],
            confidence=res["confidence"],
            language=lang,
            log_id=log.id,
        ))
    return BatchClassifyResponse(results=items)
