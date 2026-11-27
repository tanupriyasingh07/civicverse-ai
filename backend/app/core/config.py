from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CivicVerse AI"
    APP_ENV: str = "development"
    API_PORT: int = 8001
    DATABASE_URL: str = "postgresql://civicverse:civicverse_pass@localhost:5433/civicverse_db"
    REDIS_URL: str = "redis://localhost:6380/0"
    CORS_ORIGINS: str = "http://localhost:5174,http://127.0.0.1:5174"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
