"""
Test script that bypasses environment variable loading to isolate the issue.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🔧 Testing with Bypassed Environment Loading")
print("=" * 60)

# Define settings directly in code
class Settings:
    """Hardcoded settings to bypass environment loading."""
    
    # Application settings
    APP_NAME: str = "FileBoss"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./fileboss.db"
    
    def __init__(self):
        # This bypasses the pydantic validation
        pass

# Test the settings
try:
    print("\n🔄 Creating Settings instance...")
    settings = Settings()
    
    print("✅ Successfully created Settings instance")
    print(f"APP_NAME: {settings.APP_NAME}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    # Test FastAPI with these settings
    print("\n🔄 Testing FastAPI with hardcoded settings...")
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)
    
    @app.get("/")
    async def root():
        return {"message": "Hello, World! This bypasses environment loading."}
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "environment": settings.ENVIRONMENT}
    
    print("✅ FastAPI app created with hardcoded settings")
    print("\n🚀 Starting FastAPI server on http://127.0.0.1:8000")
    print("Endpoints:")
    print("  - GET /           - Simple hello world")
    print("  - GET /health     - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Test completed!")
