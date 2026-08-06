from fastapi.testclient import TestClient

from app.main import create_app


def test_application_starts() -> None:
    app = create_app()

    assert app.title == "PatchPulse API"


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_response_matches_expected_schema() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.json() == {
        "status": "healthy",
        "service": "patchpulse-api",
    }
