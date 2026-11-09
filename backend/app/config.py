from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Gmail-Manager"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = ""
    OLLAMA_MODEL: str = "qwen2.5:1.5b"

    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_TOKEN_FILE: str = "token.json"

    model_config = SettingsConfigDict(
        env_file = ("../.env", ".env"),
        extra = "ignore"
    )


setting = Settings()


