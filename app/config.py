from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    data_dir: str = "/data"
    max_bars: int = 64
    default_bpm: float = 90.0
    default_model: str = "hierarchical"
    job_ttl_seconds: int = 3600 * 24  # 24h

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
