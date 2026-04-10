"""HR Automation API Server - Configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    port: int = 3001
    host: str = "0.0.0.0"

    # Database
    database_url: str = "sqlite:///./hr_automation.db"

    # JWT
    jwt_secret: str = "dev_secret_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 1440

    # CORS - includes localhost for dev, Tauri desktop app origins
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:1420,tauri://localhost,http://localhost:*"

    # File Upload
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # LLM Configuration (Local + Remote)
    llm_provider: str = "ollama"  # "ollama" or "remote"
    llm_base_url: str = "http://localhost:11434"  # Ollama default
    llm_model: str = "qwen2.5:7b"  # Default model
    # Remote API (OpenAI-compatible)
    remote_api_key: str = ""
    remote_api_base: str = "https://api.openai.com/v1"
    remote_model: str = "gpt-4o-mini"

    # Vector Search
    embedding_model: str = "bge-large-zh-v1.5"
    qdrant_url: str = "http://localhost:6333"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()