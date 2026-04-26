from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "GymSystem Pro"
    DEBUG: bool = True
    # Soporta SQLite (local/Docker) y PostgreSQL (producción avanzada)
    DATABASE_URL: str = "sqlite:///backend/gimnasio.db"
    SECRET_KEY: str = "supersecret-gym-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # Hikvision defaults (se configuran por dispositivo en BD)
    HIKVISION_DEFAULT_PORT: int = 80
    HIKVISION_DEFAULT_USERNAME: str = "admin"
    HIKVISION_TIMEOUT: int = 10

    # Upload paths (Docker usa rutas absolutas via env var)
    UPLOAD_DIR: str = "./uploads"
    FACES_DIR: str = "./uploads/faces"

    # URL base del backend accesible desde la red local (para faceURL de Hikvision)
    # El dispositivo descarga la foto desde esta URL.
    # Ejemplo: http://192.168.1.100:8000
    # Dejar vacío para no usar faceURL (usará base64 en su lugar)
    BACKEND_BASE_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
