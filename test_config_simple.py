"""
Simplified configuration module for testing.
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union
import os
import json

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "FileBoss"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./fileboss.db"
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse CORS_ORIGINS from environment."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return ["*"]

# Create a settings instance
try:
    print("=" * 60)
    print("🔧 Testing Simplified Configuration")
    print("=" * 60)
    
    settings = Settings()
    print("✅ Successfully created settings instance")
    print(f"APP_NAME: {settings.APP_NAME}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
except Exception as e:
    print(f"❌ Error creating settings: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Test completed!")
