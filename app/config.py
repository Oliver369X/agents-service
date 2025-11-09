from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    agents_host: str = "0.0.0.0"
    agents_port: int = 5020

    gemini_api_key: str | None = None
    mistral_ocr_api_key: str | None = None

    default_locale: str = "es-BO"
    log_level: str = "INFO"
    graphiql_enabled: bool = True

    # URLs de otros microservicios
    gateway_url: str = "http://localhost:4000/graphql"
    notification_service_url: str = "http://localhost:5025/graphql"
    
    # JWT para autenticar llamadas entre servicios
    service_jwt_secret: str = "WERWRWERWERW"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()

