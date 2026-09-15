from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app configuration. All values are read from environment
    variables / a .env file so nothing is hardcoded.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://omnisure:omnisure@localhost:5432/omnisure"

    SECRET_KEY: str = "insecure-dev-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ENV: str = "development"
    DEMO_MODE: bool = True

    # Phase 2+ integrations — optional, fall back to DEMO_MODE when unset
    OPENAI_API_KEY: str | None = None
    EMAIL_SMTP_HOST: str | None = None
    EMAIL_SMTP_PORT: int | None = None
    EMAIL_SMTP_USER: str | None = None
    EMAIL_SMTP_PASSWORD: str | None = None


settings = Settings()
