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

    # eBA Integration Settings
    EBA_ENABLED: bool = False
    EBA_API_TYPE: str = "REST"  # REST or SOAP
    EBA_SOAP_URL: str = "http://localhost/eba.net/ws/ebawsapi.asmx"
    EBA_REST_URL: str = "http://localhost/eba.net/api/v1/processes"
    EBA_USER: str = "lpr_integration_user"
    EBA_PASSWORD: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

# Dynamic runtime configurations override from JSON
try:
    import json
    eba_json_path = os.path.join(settings.MEDIA_ROOT, "eba_settings.json")
    if os.path.exists(eba_json_path):
        with open(eba_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            settings.EBA_ENABLED = data.get("EBA_ENABLED", settings.EBA_ENABLED)
            settings.EBA_API_TYPE = data.get("EBA_API_TYPE", settings.EBA_API_TYPE)
            settings.EBA_SOAP_URL = data.get("EBA_SOAP_URL", settings.EBA_SOAP_URL)
            settings.EBA_REST_URL = data.get("EBA_REST_URL", settings.EBA_REST_URL)
            settings.EBA_USER = data.get("EBA_USER", settings.EBA_USER)
            settings.EBA_PASSWORD = data.get("EBA_PASSWORD", settings.EBA_PASSWORD)
except Exception:
    pass
