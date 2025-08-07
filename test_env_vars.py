"""
Script to test and debug environment variable loading.
"""
import os
import sys
from pathlib import Path
import importlib.util

print("=" * 60)
print("🔍 Testing Environment Variables")
print("=" * 60)

# Print Python and environment info
print(f"Python: {sys.version}")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Executable: {sys.executable}")

# Check if .env file exists
env_path = Path(".env")
print(f"\n🔍 Checking for .env file at: {env_path.absolute()}")
if env_path.exists():
    print("✅ .env file exists")
    print("📄 .env file content:")
    print("-" * 40)
    try:
        with open(env_path, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
    print("-" * 40)
else:
    print("❌ .env file not found")

# Check environment variables
print("\n🔍 Environment Variables:")
for var in ["CORS_ORIGINS", "ENVIRONMENT", "DEBUG", "DATABASE_URL"]:
    value = os.environ.get(var, "[Not Set]")
    print(f"{var}: {value}")

# Test dotenv loading
print("\n🔍 Testing python-dotenv loading:")
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv is installed")
    
    # Try loading .env manually
    dotenv_loaded = load_dotenv(env_path, override=True)
    print(f"   - load_dotenv() returned: {dotenv_loaded}")
    
    # Check environment variables after loading
    print("\n🔍 Environment Variables After dotenv Load:")
    for var in ["CORS_ORIGINS", "ENVIRONMENT", "DEBUG", "DATABASE_URL"]:
        value = os.environ.get(var, "[Not Set]")
        print(f"{var}: {value}")
        
except ImportError:
    print("❌ python-dotenv is not installed")

# Test pydantic-settings
print("\n🔍 Testing pydantic-settings:")
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    print("✅ pydantic-settings is importable")
    
    class TestSettings(BaseSettings):
        CORS_ORIGINS: str = "*"
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )
    
    print("✅ TestSettings class created")
    
    try:
        settings = TestSettings()
        print("✅ Successfully created TestSettings instance")
        print(f"   - CORS_ORIGINS: {settings.CORS_ORIGINS}")
        print(f"   - ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"   - DEBUG: {settings.DEBUG}")
    except Exception as e:
        print(f"❌ Error creating TestSettings instance: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Error with pydantic-settings: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Test completed!")
