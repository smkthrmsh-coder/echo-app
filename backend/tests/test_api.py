"""API endpoint smoke tests (no real API calls)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.db.database import get_engine
    from app.db.models import Base
    from app.main import app
    Base.metadata.create_all(bind=get_engine())
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_generate_without_api_key_returns_503(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY_HERE")
    from app.core.config import get_settings
    get_settings.cache_clear()
    resp = client.post("/api/generate", json={"prompt": "Motivate me"})
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]
    get_settings.cache_clear()


def test_generate_prompt_too_short(client):
    resp = client.post("/api/generate", json={"prompt": "hi"})
    assert resp.status_code == 422  # Pydantic validation error


def test_transcribe_requires_audio_file(client):
    resp = client.post("/api/transcribe")
    assert resp.status_code == 422


def test_audio_not_found(client):
    resp = client.get("/api/audio/nonexistent-id")
    assert resp.status_code == 404
