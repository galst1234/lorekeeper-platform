from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    supertokens_connection_uri: str = "http://localhost:3567"
    api_domain: str = "http://localhost:8000"
    website_domain: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173"]
    google_client_id: str = ""
    google_client_secret: str = ""
    discord_client_id: str = ""
    discord_client_secret: str = ""

    open_observe_url: str = ""
    open_observe_api_key: str = ""
    enable_tracing: bool = False
    sentry_api_dsn: str = ""


settings = Settings()  # ty: ignore[missing-argument]
