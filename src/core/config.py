from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    events_provider_base_url: str = (
        "http://events-provider.dev-2.python-labs.ru"
    )
    events_provider_api_key: str = ""
    events_provider_timeout: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
