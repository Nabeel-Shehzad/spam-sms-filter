"""Integration tests — classify endpoints."""

import pytest


@pytest.mark.asyncio
async def test_classify_spam_unauthenticated(client):
    """Classify works without a JWT (anonymous)."""
    resp = await client.post("/api/v1/classify", json={
        "text": "WINNER!! Claim your FREE £1000 prize now! Call 0800-PRIZE!"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] in ("spam", "ham")
    assert 0.0 <= body["confidence"] <= 1.0
    assert "model_used" in body
    assert "log_id" in body
    assert "language" in body


@pytest.mark.asyncio
async def test_classify_known_spam(client):
    resp = await client.post("/api/v1/classify", json={
        "text": "Win FREE cash now! Text WIN to 80080 to claim your prize!"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "spam"
    assert body["confidence"] > 0.5


@pytest.mark.asyncio
async def test_classify_known_ham(client):
    resp = await client.post("/api/v1/classify", json={
        "text": "Hey, are you joining us for lunch tomorrow at noon?"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "ham"


@pytest.mark.asyncio
async def test_classify_authenticated(auth_client):
    """Classification while logged in should still work and return a log_id."""
    resp = await auth_client.post("/api/v1/classify", json={
        "text": "Free entry in 2 a wkly comp to win FA Cup final tkts!"
    })
    assert resp.status_code == 200
    assert resp.json()["log_id"] > 0


@pytest.mark.asyncio
async def test_classify_arabic(client):
    """Arabic text should be detected and classified."""
    resp = await client.post("/api/v1/classify", json={
        "text": "مبروك! لقد فزت بجائزة كبيرة. اتصل الآن للمطالبة بها!"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] in ("spam", "ham")
    assert body["language"] == "ar"


@pytest.mark.asyncio
async def test_classify_empty_text_rejected(client):
    resp = await client.post("/api/v1/classify", json={"text": ""})
    assert resp.status_code == 422  # pydantic min_length=1


@pytest.mark.asyncio
async def test_classify_batch(client):
    resp = await client.post("/api/v1/classify/batch", json={
        "texts": [
            "Win a free iPhone! Click here now!",
            "Call me when you get home.",
            "Congratulations! You have been selected for a cash prize!",
        ]
    })
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 3
    for r in results:
        assert r["label"] in ("spam", "ham")
        assert 0.0 <= r["confidence"] <= 1.0
        assert r["log_id"] > 0


@pytest.mark.asyncio
async def test_classify_batch_empty_rejected(client):
    resp = await client.post("/api/v1/classify/batch", json={"texts": []})
    assert resp.status_code == 422
