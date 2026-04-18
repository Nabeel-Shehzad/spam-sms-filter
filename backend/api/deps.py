"""FastAPI dependency injection helpers."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import decode_token
from backend.db.crud import get_user_by_email
from backend.db.database import get_db
from backend.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exc
        email: str = payload.get("email", "")
    except JWTError:
        raise credentials_exc

    user = await get_user_by_email(db, email)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


async def get_optional_user(
    token: str | None = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        email: str = payload.get("email", "")
        return await get_user_by_email(db, email)
    except JWTError:
        return None
