from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="API_")

    app_name: str = "media-proxy-api"
    cors_origins: list[str] = ["http://localhost:5173"]
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "media_proxy"
    crawl_timeout_seconds: float = 15.0


settings = Settings()
