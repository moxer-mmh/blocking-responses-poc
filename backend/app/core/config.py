"""Application configuration and settings."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # OpenAI Configuration
    openai_api_key: str = ""
    default_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    
    # Logging Configuration
    log_level: str = "INFO"

    # SSE and buffering settings
    delay_tokens: int = 24
    delay_ms: int = 250

    # Sliding Window Analysis Settings
    analysis_window_size: int = 150  # tokens to analyze at once for compliance
    analysis_overlap: int = 50       # tokens overlap between analysis windows
    analysis_frequency: int = 25     # analyze every N tokens (instead of every token)
    
    # Compliance thresholds
    risk_threshold: float = 0.7  # Fixed default to match env file
    presidio_confidence_threshold: float = 0.6
    judge_threshold: float = 0.8
    enable_judge: bool = True

    # Safe rewrite settings
    enable_safe_rewrite: bool = True
    rewrite_temperature: float = 0.2

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./compliance_audit.db"
    
    # Security and privacy settings
    hash_sensitive_data: bool = True
    
    # CORS settings
    cors_origins: str = "*"
    
    # Rate limiting
    rate_limit: str = "100/minute"
    
    # Security settings
    secret_key: str = Field(default_factory=lambda: os.urandom(32).hex())


# Global settings instance
settings = Settings()
