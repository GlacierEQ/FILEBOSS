"""
Application Configuration

This module handles configuration settings for the application.
Uses pydantic_settings to manage environment variables and settings.
"""
import os
from typing import List, Optional
from pydantic import AnyHttpUrl, validator, PostgresDsn
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "CaseBuilder"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-this-in-production"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CaseBuilder API"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "casebuilder"
    DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """Assemble the database connection string."""
        if isinstance(v, str):
            return v
        
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                path=f"/{values.get('POSTGRES_DB') or ''}",
            )
        )
    
    # File storage settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 100  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",  # PDF
        "image/jpeg", "image/png", "image/gif",  # Images
        "text/plain", "text/csv",  # Text files
        "application/json", "application/xml",  # Data files
        "application/zip", "application/x-rar-compressed",  # Archives
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    ]
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # FileBoss settings
    FILEBOSS_BASE_DIR: str = "/var/fileboss"
    FILEBOSS_PROCESSING_TIMEOUT: int = 300  # 5 minutes
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the settings instance."""
    return settings
