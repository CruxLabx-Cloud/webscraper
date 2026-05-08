from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # External APIs
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Database — defaults to local sqlite for zero-config dev/test
    database_url: str = "sqlite+aiosqlite:///./citracker.db"

    # Auth
    jwt_secret: str = "change-me-in-prod-please-set-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # SMTP — leave empty to log emails instead of sending
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Company Intelligence <noreply@citracker.local>"
    smtp_use_tls: bool = True

    # App
    app_base_url: str = "http://localhost:3000"
    scheduler_enabled: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
