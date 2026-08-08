from app.core.config import Settings


def test_database_url_is_loaded_from_environment(monkeypatch) -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/patchpulse_test"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()

    assert settings.database_url.get_secret_value() == database_url


def test_external_service_settings_are_environment_driven(monkeypatch) -> None:
    monkeypatch.setenv("PATCHPULSE_OSV_API_URL", "https://osv.internal.test")
    monkeypatch.setenv("PATCHPULSE_OSV_READ_TIMEOUT_SECONDS", "9")
    settings = Settings()
    assert settings.osv_api_url == "https://osv.internal.test"
    assert settings.osv_read_timeout_seconds == 9
