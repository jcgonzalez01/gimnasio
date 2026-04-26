from pydantic_settings import BaseSettings
from typing import Optional, List
import secrets


_DEFAULT_DEV_SECRET = "supersecret-gym-key-change-in-production"


class Settings(BaseSettings):
    APP_NAME: str = "GymSystem Pro"
    DEBUG: bool = True
    ENV: str = "development"  # development | production

    # Soporta SQLite (local/Docker) y PostgreSQL (producción avanzada)
    DATABASE_URL: str = "sqlite:///backend/gimnasio.db"
    SECRET_KEY: str = _DEFAULT_DEV_SECRET
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # CORS — lista separada por comas. "*" en dev, dominios concretos en prod.
    CORS_ORIGINS: str = "*"

    # Hikvision defaults (se configuran por dispositivo en BD)
    HIKVISION_DEFAULT_PORT: int = 80
    HIKVISION_DEFAULT_USERNAME: str = "admin"
    HIKVISION_TIMEOUT: int = 10

    # Upload paths (Docker usa rutas absolutas via env var)
    UPLOAD_DIR: str = "./uploads"
    FACES_DIR: str = "./uploads/faces"

    # URL base del backend accesible desde la red local (para faceURL de Hikvision)
    BACKEND_BASE_URL: str = ""

    # ── Email (SMTP) — opcional, para notificaciones ──────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    EMAIL_NOTIFICATIONS_ENABLED: bool = False

    # Días antes del vencimiento para enviar recordatorio
    EXPIRY_REMINDER_DAYS: str = "7,3,1"  # múltiples valores separados por coma

    # ── Bootstrap admin (se crea en startup si no hay usuarios) ──────────────
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = "admin123"  # cambiar tras primer login
    BOOTSTRAP_ADMIN_EMAIL: str = ""

    # ── Pasarela de pago (opcional) ───────────────────────────────────────────
    MERCADOPAGO_ACCESS_TOKEN: str = ""
    MERCADOPAGO_PUBLIC_KEY: str = ""
    PAYMENT_PROVIDER: str = "manual"  # manual | mercadopago

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() in ("", "*"):
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def expiry_reminder_days_list(self) -> List[int]:
        try:
            return sorted({int(x.strip()) for x in self.EXPIRY_REMINDER_DAYS.split(",")
                           if x.strip().isdigit()}, reverse=True)
        except Exception:
            return [7, 3, 1]

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    def validate_for_production(self) -> List[str]:
        """Devuelve la lista de problemas de configuración bloqueantes en producción."""
        errors: List[str] = []
        if self.is_production:
            if self.SECRET_KEY == _DEFAULT_DEV_SECRET or len(self.SECRET_KEY) < 32:
                errors.append("SECRET_KEY debe ser fuerte en producción (genera con `openssl rand -hex 32`).")
            if "*" in self.cors_origins_list:
                errors.append("CORS_ORIGINS no puede ser '*' en producción.")
            if self.BOOTSTRAP_ADMIN_PASSWORD == "admin123":
                errors.append("BOOTSTRAP_ADMIN_PASSWORD por defecto detectada — cámbiala antes del primer arranque.")
        return errors

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
