from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    agents_host: str = "localhost"
    agents_port: int = 5020

    gemini_api_key: str | None = None
    mistral_ocr_api_key: str | None = None
    gemini_dev_mode: bool = False  # When True, return fallback responses for 503/timeouts in dev/test

    default_locale: str = "es-BO"
    log_level: str = "INFO"
    graphiql_enabled: bool = True

    # URLs de otros microservicios
    gateway_url: str = "http://localhost:4000/graphql"
    notification_service_url: str = "https://seal-app-44emn.ondigitalocean.app/graphql"
    
    # JWT para autenticar llamadas entre servicios 
    service_jwt_secret: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjY0MGJjMWViOGU3MjI2Mjc4MDg4OTlhNmI3OTFhNDhmIn0.eyJ1c2VySWQiOiJNaWNhZWwiLCJwZXJtaXNzaW9ucyI6ImFkbWluIiwiYXV0aG9yaXphdGlvbiI6ImRrc2xhZmprbHNkYWpmZHNmIn0.ZpNcIaMIzvZl0i5GwSIkBOBHcF3tJctEuCrBPD6kEyKEqIcoIhZkZRqUJgXHrpsV-hitSNKx0GVbn6ZlGeBHWg"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()

