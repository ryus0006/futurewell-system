from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, overridable via environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "onboarding-backend"
    # Origins allowed to call the API (Angular dev server + direct API access).
    # In Coolify, override with your real frontend domain via the CORS_ORIGINS env var.
    cors_origins: list[str] = [
        "http://localhost:4200",
        "http://localhost:8000",
    ]

    # Async SQLAlchemy URL for the MySQL user database.
    # Local default targets the DB from docker-compose.local.yml; in Coolify this
    # is injected from the managed MySQL resource via the DATABASE_URL env var.
    database_url: str = "mysql+aiomysql://appuser:apppass@localhost:3306/appdb"


settings = Settings()
