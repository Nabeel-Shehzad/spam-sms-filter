"""
Shared pytest fixtures for integration tests.

Uses an in-memory SQLite database so tests are fully isolated —
no real PostgreSQL or file-based DB needed.
"""

import os
import pytest
import pytest_asyncio

# Point to in-memory SQLite before any app imports touch the env
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.api.main import app
from backend.db.database import Base, get_db


# ── in-memory DB engine (shared across the whole test session) ─────────────

_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def _override_get_db():
    async with _SessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all DB tables once per test session."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired directly to the FastAPI ASGI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client):
    """Client that is already registered and has a valid JWT token."""
    import uuid
    email = f"fixture_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "fixPass123",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
