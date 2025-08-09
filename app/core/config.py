import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, PostgresDsn, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "FileBoss"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Security
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Server
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # FastAPI backend
    ]
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fileboss")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble the database connection string."""
        if isinstance(v, str):
            return v
            
        # Construct the database URL from components
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"  # Format: "requests/window_in_seconds"
    RATE_LIMIT_OVERRIDES: Dict[str, str] = {
        "/api/v1/auth/": "10/minute",
        "/api/v1/users/": "30/minute"
    }
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "text"
    LOG_FILE: Optional[str] = "logs/app.log"
    
    # First Superuser
    FIRST_SUPERUSER_EMAIL: EmailStr = os.getenv("FIRST_SUPERUSER_EMAIL", "admin@example.com")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "changethis")
    USERS_OPEN_REGISTRATION: bool = False
    
    # File Storage
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: List[str] = ["txt", "pdf", "png", "jpg", "jpeg", "gif"]
    
    # Email (optional, for password reset)
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5 minutes
    
    class Config:
        case_sensitive = True
        env_file = ".env"
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return []
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                user=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                path=f"/{values.get('POSTGRES_DB') or ''}",
            )
        )
    
    @validator("UPLOAD_FOLDER", pre=True)
    def create_upload_folder(cls, v: str) -> str:
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"


# Create settings instance
settings = Settings()

# Configure logging
if settings.is_testing:
    settings.LOG_LEVEL = "CRITICAL"
elif settings.is_development:
    settings.LOG_LEVEL = "DEBUG"

# Ensure the upload folder exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
