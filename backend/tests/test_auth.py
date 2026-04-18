"""Integration tests — auth routes (register / login / refresh / TOTP)."""

import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new_user@example.com",
        "password": "SecurePass1",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "SecurePass1"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "short",
    })
    assert resp.status_code == 422  # pydantic validation


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "email": "login_ok@example.com", "password": "Password99",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login_ok@example.com", "password": "Password99",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "badpass@example.com", "password": "RealPass99",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "badpass@example.com", "password": "WrongPass!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com", "password": "AnyPass99",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    reg = await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com", "password": "RefreshPass1",
    })
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_totp_setup_requires_auth(client):
    resp = await client.post("/api/v1/auth/totp/setup")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_totp_setup_and_verify(auth_client):
    # Setup TOTP
    setup = await auth_client.post("/api/v1/auth/totp/setup")
    assert setup.status_code == 200
    data = setup.json()
    assert "secret" in data
    assert "uri" in data

    # Verify with correct code
    import pyotp
    code = pyotp.TOTP(data["secret"]).now()
    verify = await auth_client.post("/api/v1/auth/totp/verify", json={"code": code})
    assert verify.status_code == 200
