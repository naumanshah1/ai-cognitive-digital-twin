
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
        "version": "0.1.0",
    }


def test_openapi_documentation_is_available():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "AI Cognitive Digital Twin"
    assert "/health" in schema["paths"]
    assert "/health/ready" in schema["paths"]
    assert "/api/v1/agent/run" in schema["paths"]
