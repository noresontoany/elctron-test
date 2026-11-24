from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    session_secret: str
    electric_secret: str
    electric_url: str = "http://electric:3000"
    sync_max_connections: int = Field(default=128, ge=4, le=10000)
    sync_admission_timeout: float = Field(default=0.25, gt=0, le=10)
    app_extra_origins: str = ""
    app_origin: str = "http://localhost:8097"


@lru_cache
def get_settings() -> Settings:
    return Settings()
