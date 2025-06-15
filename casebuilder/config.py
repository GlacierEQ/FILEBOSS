"""
Configuration management for Mega CaseBuilder 3000.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite+aiosqlite:///./casebuilder.db",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy engine echo"
    )
    pool_size: int = Field(
        default=5,
        description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=10,
        description="Maximum overflow for connection pool"
    )


class StorageSettings(BaseModel):
    """File storage configuration."""
    
    base_path: Path = Field(
        default=Path("./data"),
        description="Base path for file storage"
    )
    temp_path: Path = Field(
        default=Path("./temp"),
        description="Temporary file storage path"
    )
    allowed_extensions: List[str] = Field(
        default=[
            # Documents
            ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
            # Spreadsheets
            ".xls", ".xlsx", ".ods", ".csv",
            # Presentations
            ".ppt", ".pptx", ".odp",
            # Images
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
            # Audio
            ".mp3", ".wav", ".ogg", ".m4a", ".flac",
            # Video
            ".mp4", ".mov", ".avi", ".mkv", ".webm",
            # Archives
            ".zip", ".rar", ".7z", ".tar", ".gz"
        ],
        description="Allowed file extensions for upload"
    )
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum file size in bytes"
    )


class AISettings(BaseModel):
    """AI and ML related configuration."""
    
    provider: str = Field(
        default="openai",
        description="Default AI provider (openai, anthropic, etc.)"
    )
    model: str = Field(
        default="gpt-4-turbo-preview",
        description="Default AI model to use"
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for AI generation"
    )
    max_tokens: int = Field(
        default=4000,
        description="Maximum tokens to generate"
    )


class APISettings(BaseModel):
    """API related configuration."""
    
    title: str = "Mega CaseBuilder 3000 API"
    description: str = "Advanced Legal Case Management System"
    version: str = "0.1.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    debug: bool = False
    cors_origins: List[str] = ["*"]
    api_prefix: str = "/api/v1"


class SecuritySettings(BaseModel):
    """Security related configuration."""
    
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT token generation"
    )
    algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT token generation"
    )
    access_token_expire_minutes: int = Field(
        default=60 * 24 * 7,  # 7 days
        description="Access token expiration time in minutes"
    )
    password_min_length: int = Field(
        default=12,
        description="Minimum password length"
    )


class Settings(BaseSettings):
    """Application settings."""
    
    # Core settings
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    
    # App settings
    app_name: str = "Mega CaseBuilder 3000"
    app_version: str = "0.1.0"
    
    # Module configurations
    database: DatabaseSettings = DatabaseSettings()
    storage: StorageSettings = StorageSettings()
    ai: AISettings = AISettings()
    api: APISettings = APISettings()
    security: SecuritySettings = SecuritySettings()
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


# Global settings instance
settings = Settings()
