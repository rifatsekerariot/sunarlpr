import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://lpr_user:lpr_password@postgres:5432/lpr_db"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "supersecretjwtkeyforlprproject2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    LOG_LEVEL: str = "info"
    MEDIA_ROOT: str = "/app/media"

    class Config:
        env_file = ".env"

settings = Settings()
