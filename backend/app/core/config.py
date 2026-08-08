from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="PatchPulse API")
    environment: str = Field(default="local")
    api_prefix: str = Field(default="/api/v1")
    allowed_frontend_origin: str = Field(default="http://localhost:5173")
    database_url: SecretStr = Field(validation_alias="DATABASE_URL")
    dev_user_email: str = Field(default="dev@patchpulse.local")
    github_token: SecretStr | None = Field(default=None, validation_alias="GITHUB_TOKEN")
    github_api_url: str = Field(default="https://api.github.com")
    github_connect_timeout_seconds: float = Field(default=5.0, gt=0)
    github_read_timeout_seconds: float = Field(default=15.0, gt=0)
    requirements_max_bytes: int = Field(default=1_000_000, gt=0)
    osv_api_url: str = Field(default="https://api.osv.dev")
    osv_connect_timeout_seconds: float = Field(default=5.0, gt=0)
    osv_read_timeout_seconds: float = Field(default=20.0, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PATCHPULSE_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
