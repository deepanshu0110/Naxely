from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str
    MASTER_ENCRYPTION_KEY: str = ""
    ENCRYPTION_SALT: str = ""

    DODO_API_KEY: str = ""
    DODO_WEBHOOK_SECRET: str = ""
    DODO_PRO_PRODUCT_ID: str = ""
    DODO_AGENCY_PRODUCT_ID: str = ""
    DODO_ENVIRONMENT: str = "test_mode"
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "hello@databrief.io"

    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    SECRET_KEY: str
    TEMP_DIR: str = "/tmp/databrief"

    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""

    SENTRY_DSN: str = ""

    SUPABASE_DB_HOST: str = ""
    SUPABASE_DB_PORT: int = 5432
    SUPABASE_DB_NAME: str = "postgres"
    SUPABASE_DB_USER: str = "postgres"
    SUPABASE_DB_PASSWORD: str = ""

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.SUPABASE_DB_USER}:{self.SUPABASE_DB_PASSWORD}"
            f"@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()  # type: ignore[call-arg]
