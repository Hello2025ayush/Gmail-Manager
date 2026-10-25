from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Gmail-Manager"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file = ("../.env", ".env"),
        extra = "ignore"
    )


setting = Settings()

    