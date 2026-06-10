from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    open_observe_url: str = ""
    open_observe_api_key: str = ""
    enable_tracing: bool = False
    sentry_dsn: str = ""


settings = Settings()
