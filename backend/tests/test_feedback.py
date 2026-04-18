"""Integration tests — feedback submission and stats."""

import pytest


async def _classify_and_get_log_id(client, text: str) -> int:
    resp = await client.post("/api/v1/classify", json={"text": text})
    assert resp.status_code == 200
    return resp.json()["log_id"]


@pytest.mark.asyncio
async def test_submit_feedback_spam(client):
    log_id = await _classify_and_get_log_id(
        client, "Win FREE cash now! Call 0900-WINNER to claim!"
    )
    resp = await client.post("/api/v1/feedback", json={
        "log_id": log_id,
        "correct_label": "spam",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["log_id"] == log_id
    assert body["correct_label"] == "spam"
    assert "submitted_at" in body


@pytest.mark.asyncio
async def test_submit_feedback_ham(client):
    log_id = await _classify_and_get_log_id(client, "Hey mum, I'll be home by 6.")
    resp = await client.post("/api/v1/feedback", json={
        "log_id": log_id,
        "correct_label": "ham",
    })
    assert resp.status_code == 201
    assert resp.json()["correct_label"] == "ham"


@pytest.mark.asyncio
async def test_feedback_update_idempotent(client):
    """Submitting feedback twice on the same log_id updates rather than errors."""
    log_id = await _classify_and_get_log_id(client, "Urgent! You owe taxes. Pay now to avoid arrest!")
    await client.post("/api/v1/feedback", json={"log_id": log_id, "correct_label": "spam"})
    resp = await client.post("/api/v1/feedback", json={"log_id": log_id, "correct_label": "ham"})
    assert resp.status_code == 201
    assert resp.json()["correct_label"] == "ham"


@pytest.mark.asyncio
async def test_feedback_invalid_label(client):
    log_id = await _classify_and_get_log_id(client, "Some random message here.")
    resp = await client.post("/api/v1/feedback", json={
        "log_id": log_id,
        "correct_label": "unknown",  # must be spam|ham
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_stats_returns_correct_counts(client):
    # Classify a pair of known messages
    await client.post("/api/v1/classify", json={"text": "WIN FREE PRIZE NOW! CALL 0800!"})
    await client.post("/api/v1/classify", json={"text": "See you at the meeting at 3pm."})

    resp = await client.get("/api/v1/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 2
    assert body["spam_count"] >= 0
    assert body["ham_count"] >= 0
    assert body["spam_count"] + body["ham_count"] == body["total"]


@pytest.mark.asyncio
async def test_history_returns_list(client):
    resp = await client.get("/api/v1/stats/history?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "id" in item
        assert "predicted_label" in item
        assert "confidence" in item
        assert "created_at" in item
