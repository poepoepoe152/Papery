"""Application configuration.

Settings are read from environment variables (see docker-compose.yml) with
sensible local-development defaults so the app is runnable out of the box.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Papery"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://papery:papery@db:5432/papery"

    # JWT / Auth
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS (comma-separated list of allowed origins)
    CORS_ORIGINS: str = "http://localhost:3000"

    # Seeded platform super-admin
    SUPER_ADMIN_EMAIL: str = "admin@papery.app"
    SUPER_ADMIN_PASSWORD: str = "Admin123!"

    # License
    LICENSE_DURATION_DAYS: int = 365

    # Password reset + email delivery (optional SMTP; falls back to logging)
    FRONTEND_URL: str = "http://localhost:3000"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@papery.app"

    # File storage (local volume; S3 is the production target)
    STORAGE_DIR: str = "/app/uploads"
    MAX_UPLOAD_MB: int = 25

    # Optional LLM semantic-comparison hook. Empty => deterministic-only.
    OPENAI_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
