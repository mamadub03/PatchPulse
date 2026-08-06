from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.routes import readiness
from app.db.session import get_db_session
from app.main import create_app


def test_health_does_not_require_database_query(monkeypatch) -> None:
    def fail_if_called(session: object) -> None:
        raise AssertionError("health should not query the database")

    monkeypatch.setattr(readiness, "check_database_connection", fail_if_called)
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_readiness_returns_ok_when_database_check_succeeds(monkeypatch) -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: object()
    monkeypatch.setattr(readiness, "check_database_connection", lambda session: None)
    client = TestClient(app)

    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


def test_readiness_returns_safe_503_when_database_check_fails(monkeypatch) -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: object()

    def fail_database_check(session: object) -> None:
        raise OperationalError(
            statement="SELECT 1",
            params=None,
            orig=RuntimeError("password=secret host=localhost failed"),
        )

    monkeypatch.setattr(readiness, "check_database_connection", fail_database_check)
    client = TestClient(app)

    response = client.get("/api/v1/readiness")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}
    assert "secret" not in response.text
    assert "localhost" not in response.text
    assert "SELECT 1" not in response.text
