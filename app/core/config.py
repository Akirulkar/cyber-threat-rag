# app/core/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Base Directory Resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Cybersecurity Threat Intelligence Assistant"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Security / API Auth
    API_KEY_SECRET: Optional[str] = (
        "cybersec-secret-key-123"  # Change this in your .env
    )

    # Environment Variables from your previous config
    NVD_API_KEY: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    DATA_DIR: str = "data/raw"

    # RAG / Model Defaults
    NVIDIA_MODEL: str = "nvidia/nemotron-3-nano-30b-a3b"
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
