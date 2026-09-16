"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to VeriFeed API"}


def test_health_check_endpoint():
    """Verify /health endpoint returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_stories_endpoint():
    """Verify /api/v1/stories endpoint returns list structure."""
    response = client.get("/api/v1/stories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_sources_endpoint():
    """Verify /api/v1/sources endpoint returns list structure."""
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_recent_verifications_endpoint():
    """Verify /api/v1/verify/recent endpoint returns list structure."""
    response = client.get("/api/v1/verify/recent")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_institutional_alerts_endpoint():
    """Verify /api/v1/institutions/alerts endpoint returns list structure."""
    response = client.get("/api/v1/institutions/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_submit_scam_endpoint():
    """Verify posting a user scam submission returns success status."""
    payload = {
        "submitted_text": "Suspicious SMS claiming free $500 loan from bank if I click link bit.ly/fake-bank",
        "contact_info": "test@example.com"
    }
    response = client.post("/api/v1/institutions/submissions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "submission_id" in data


def test_search_stories_endpoint():
    """Verify /api/v1/stories/search?q=... returns list structure."""
    response = client.get("/api/v1/stories/search?q=politics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_stories_requires_q():
    """Verify /api/v1/stories/search without q= returns 422 validation error."""
    response = client.get("/api/v1/stories/search")
    assert response.status_code == 422


def test_get_story_not_found():
    """Verify /api/v1/stories/{id} returns 404 for a non-existent story."""
    response = client.get("/api/v1/stories/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Story not found"
