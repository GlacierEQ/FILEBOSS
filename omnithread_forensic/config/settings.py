"""
Core configuration and settings for Omnithread Forensic Protocol.
Handles environment variables, logging, and runtime configuration.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseSettings, Field, HttpUrl, validator
from pydantic.types import SecretStr

# Base directory
BASE_DIR = Path(__file__).parent.parent.resolve()

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    APP_NAME: str = "Omnithread Forensic Protocol"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Storage
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # Cloud API Credentials (will be loaded from environment variables)
    GOOGLE_DRIVE_CREDENTIALS: Optional[Dict] = None
    DROPBOX_ACCESS_TOKEN: Optional[SecretStr] = None
    ONEDRIVE_CLIENT_ID: Optional[str] = None
    ONEDRIVE_CLIENT_SECRET: Optional[SecretStr] = None
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/omnithread.db"
    
    # Agent Configuration
    AGENT_TIMEOUT: int = 300  # seconds
    MAX_WORKERS: int = 8
    
    # File Processing
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FILE_TYPES: List[str] = [
        # Documents
        ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".xlsx", ".xls",
        ".pptx", ".ppt", ".csv", ".json", ".xml",
        # Images
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
        # Audio/Video
        ".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi", ".mkv",
        # Archives
        ".zip", ".rar", ".7z", ".tar", ".gz"
    ]
    
    # OCR Configuration
    ENABLE_OCR: bool = True
    TESSERACT_CMD: Optional[str] = None
    
    # Logging Configuration
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("DATA_DIR", "CACHE_DIR", "LOGS_DIR", pre=True)
    def create_dirs(cls, v: Union[str, Path]) -> Path:
        """Ensure directories exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        v = v.upper()
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        return v

# Initialize settings
settings = Settings()

# Configure logging
def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.LOGS_DIR / "omnithread.log")
        ]
    )
    
    # Suppress noisy loggers
    for logger_name in ["urllib3", "botocore", "boto3"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

# Run setup when module is imported
setup_logging()

# Create a logger for this module
logger = logging.getLogger(__name__)
