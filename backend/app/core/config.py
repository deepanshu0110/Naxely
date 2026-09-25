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
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_API_KEY: str = ""
    # House AI key for Free tier (BYOK not required). Backend-only secret —
    # never sent to the frontend, never logged. Kill switch: when
    # FREE_TIER_HOUSE_KEY_ENABLED is false, Free falls back to BYOK-required.
    # Groq only, no fallback (Mistral/Cerebras need PAYG, GitHub Models is
    # retired, ModelScope needs a CN phone, Gemini trains on free-tier data).
    # Mistral stays available as a Pro/Agency BYOK option via PROVIDER_CONFIG.
    HOUSE_AI_KEY_GROQ: str = ""
    FREE_TIER_HOUSE_KEY_ENABLED: bool = True
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    RESEND_API_KEY: str = ""
    RESEND_WEBHOOK_SECRET: str = ""
    FROM_EMAIL: str = "hello@naxely.com"

    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = ""
    SECRET_KEY: str
    CRON_SECRET: str = ""
    LIFECYCLE_CRON_SECRET: str = ""

    @property
    def resolved_allowed_origins(self) -> str:
        return self.ALLOWED_ORIGINS or self.FRONTEND_BASE_URL

    TEMP_DIR: str = "/tmp/naxely"

    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""

    SENTRY_DSN: str = ""

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

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
