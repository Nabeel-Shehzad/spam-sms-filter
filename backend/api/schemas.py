"""Pydantic request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str


class TOTPVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1600)


class ClassifyResponse(BaseModel):
    label: Literal["spam", "ham"]
    confidence: float
    model_used: str
    language: str
    log_id: int


class BatchClassifyRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=100)


class BatchClassifyItem(BaseModel):
    text: str
    label: Literal["spam", "ham"]
    confidence: float
    language: str
    log_id: int


class BatchClassifyResponse(BaseModel):
    results: list[BatchClassifyItem]


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    log_id: int
    correct_label: Literal["spam", "ham"]


class FeedbackResponse(BaseModel):
    id: int
    log_id: int
    correct_label: str
    submitted_at: datetime


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    total: int
    spam_count: int
    ham_count: int
    feedback_accuracy: float | None
    feedback_count: int


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class LogItem(BaseModel):
    id: int
    message_text: str
    predicted_label: str
    confidence: float
    model_used: str
    language: str
    created_at: datetime

    class Config:
        from_attributes = True
