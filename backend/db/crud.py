"""CRUD operations for all ORM models."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ClassificationLog, Feedback, User


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_totp(db: AsyncSession, user: User, secret: str, enabled: bool) -> User:
    user.totp_secret = secret
    user.totp_enabled = enabled
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# ClassificationLog
# ---------------------------------------------------------------------------

async def create_log(
    db: AsyncSession,
    message_text: str,
    predicted_label: str,
    confidence: float,
    model_used: str,
    language: str = "en",
    user_id: int | None = None,
) -> ClassificationLog:
    log = ClassificationLog(
        message_text=message_text,
        predicted_label=predicted_label,
        confidence=confidence,
        model_used=model_used,
        language=language,
        user_id=user_id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_recent_logs(
    db: AsyncSession, user_id: int | None = None, limit: int = 50
) -> list[ClassificationLog]:
    q = select(ClassificationLog).order_by(ClassificationLog.created_at.desc()).limit(limit)
    if user_id is not None:
        q = q.where(ClassificationLog.user_id == user_id)
    result = await db.execute(q)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

async def get_stats(db: AsyncSession, user_id: int | None = None) -> dict:
    q = select(ClassificationLog)
    if user_id is not None:
        q = q.where(ClassificationLog.user_id == user_id)
    result = await db.execute(q)
    logs = list(result.scalars().all())

    total = len(logs)
    spam_count = sum(1 for l in logs if l.predicted_label == "spam")
    ham_count = total - spam_count

    # Feedback-corrected accuracy
    feedback_q = select(Feedback)
    fb_result = await db.execute(feedback_q)
    feedbacks = {fb.log_id: fb.correct_label for fb in fb_result.scalars().all()}

    correct = 0
    evaluated = 0
    for log in logs:
        if log.id in feedbacks:
            evaluated += 1
            if feedbacks[log.id] == log.predicted_label:
                correct += 1

    feedback_accuracy = (correct / evaluated * 100) if evaluated else None

    return {
        "total": total,
        "spam_count": spam_count,
        "ham_count": ham_count,
        "feedback_accuracy": feedback_accuracy,
        "feedback_count": len(feedbacks),
    }


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

async def create_feedback(
    db: AsyncSession, log_id: int, correct_label: str
) -> Feedback:
    existing = await db.execute(select(Feedback).where(Feedback.log_id == log_id))
    fb = existing.scalar_one_or_none()
    if fb:
        fb.correct_label = correct_label
    else:
        fb = Feedback(log_id=log_id, correct_label=correct_label)
        db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return fb
