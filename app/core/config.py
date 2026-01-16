from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "users"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Database Pool
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10
    db_pool_timeout: int = 30

    # Activation
    activation_code_length: int = 4
    activation_code_expiry_minutes: int = 1

    # API
    api_title: str = "User Registration API"
    api_description: str = "API for user registration and activation"
    api_version: str = "0.1.0"

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Global settings instance
settings = Settings()
