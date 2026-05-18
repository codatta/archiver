from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "contributor-portal-api"
    assert "config" in body


def test_health_includes_feature_flags():
    response = client.get("/v1/health")
    config = response.json()["config"]
    assert "campaign_source" in config
    assert "attempt_index_backend" in config
    assert "lineage_backend" in config
    assert "vision_engine_url" in config
