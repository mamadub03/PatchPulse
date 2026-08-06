from app.core.config import Settings


def test_database_url_is_loaded_from_environment(monkeypatch) -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/patchpulse_test"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()

    assert settings.database_url.get_secret_value() == database_url
