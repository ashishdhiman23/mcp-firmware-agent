"""Configuration settings for the MCP Firmware Log Analysis Server."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.3
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # File Upload Configuration
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_log_extensions: list = [".log", ".txt", ".json"]
    allowed_elf_extensions: list = [".elf", ".bin"]
    
    # Analysis Configuration
    max_log_lines: int = 10000
    chunk_size: int = 1000
    confidence_threshold: float = 0.5
    
    # Paths
    upload_dir: str = "uploads"
    reports_dir: str = "reports"
    templates_dir: str = "templates"
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings 