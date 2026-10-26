from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Gmail-Manager"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = ""

    GOOGLE_CREDENTIALS_FILE: str
    GOOGLE_TOKEN_FILE: str

    model_config = SettingsConfigDict(
        env_file = ("../.env", ".env"),
        extra = "ignore"
    )


setting = Settings()

    