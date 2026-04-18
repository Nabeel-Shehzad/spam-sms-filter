"""SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    logs: Mapped[list["ClassificationLog"]] = relationship(
        "ClassificationLog", back_populates="user", cascade="all, delete-orphan"
    )


class ClassificationLog(Base):
    __tablename__ = "classification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(10), nullable=False)   # "spam" | "ham"
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_used: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User | None"] = relationship("User", back_populates="logs")
    feedback: Mapped["Feedback | None"] = relationship(
        "Feedback", back_populates="log", cascade="all, delete-orphan", uselist=False
    )


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    log_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classification_logs.id", ondelete="CASCADE"), unique=True
    )
    correct_label: Mapped[str] = mapped_column(String(10), nullable=False)  # "spam" | "ham"
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    log: Mapped["ClassificationLog"] = relationship("ClassificationLog", back_populates="feedback")
