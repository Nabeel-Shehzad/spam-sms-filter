"""Auth routes: register, login, token refresh, TOTP setup/verify."""

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TOTPSetupResponse,
    TOTPVerifyRequest,
    TokenResponse,
)
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token
from backend.auth.password import hash_password, verify_password
from backend.auth.totp import generate_totp_secret, get_totp_uri, verify_totp
from backend.db.crud import create_user, get_user_by_email, update_totp
from backend.db.database import get_db
from backend.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await get_user_by_email(db, body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = await create_user(db, body.email, hash_password(body.password))
    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    from sqlalchemy import select
    from backend.db.models import User as UserModel
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return TokenResponse(
        access_token=create_access_token(user.id, user.email),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, current_user.email)
    await update_totp(db, current_user, secret, enabled=False)
    return TOTPSetupResponse(secret=secret, uri=uri)


@router.post("/totp/verify")
async def verify_totp_code(
    body: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.totp_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "TOTP not set up")
    if not verify_totp(current_user.totp_secret, body.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid TOTP code")
    await update_totp(db, current_user, current_user.totp_secret, enabled=True)
    return {"message": "2FA enabled successfully"}
