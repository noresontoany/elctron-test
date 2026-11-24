from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    session_secret: str
    electric_secret: str
    electric_url: str = "http://electric:3000"
    app_origin: str = "http://localhost:8097"


@lru_cache
def get_settings() -> Settings:
    return Settings()
