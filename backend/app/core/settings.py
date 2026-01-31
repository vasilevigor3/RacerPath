from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://racerpath:racerpath@localhost:5432/racerpath",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app_env: str = os.getenv("APP_ENV", "local")
    port: int = int(os.getenv("PORT", "8000"))
    classification_version: str = os.getenv("CLASSIFICATION_VERSION", "1.0.0")
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    bootstrap_key: str = os.getenv("BOOTSTRAP_KEY", "change-me")
    auth_rate_limit_per_minute: int = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10"))
    ingest_payload_max_bytes: int = int(os.getenv("INGEST_PAYLOAD_MAX_BYTES", "250000"))
    anti_gaming_min_multiplier: float = float(os.getenv("ANTI_GAMING_MIN_MULTIPLIER", "0.5"))
    anti_gaming_max_multiplier: float = float(os.getenv("ANTI_GAMING_MAX_MULTIPLIER", "1.5"))
    wss_events_url: str | None = os.getenv("WSS_EVENTS_URL") or None
    wss_api_key: str | None = os.getenv("WSS_API_KEY") or None
    gridfinder_events_url: str | None = os.getenv("GRIDFINDER_EVENTS_URL") or None
    gridfinder_api_key: str | None = os.getenv("GRIDFINDER_API_KEY") or None


settings = Settings()
