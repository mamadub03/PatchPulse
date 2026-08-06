from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="PatchPulse API")
    environment: str = Field(default="local")
    api_prefix: str = Field(default="/api/v1")
    allowed_frontend_origin: str = Field(default="http://localhost:5173")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PATCHPULSE_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
