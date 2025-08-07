"""
Focused test script to debug the Settings class and environment variable loading.
"""
import os
import sys
from pathlib import Path
import importlib
import traceback

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variables for testing
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"

print("=" * 60)
print("🔍 Testing Settings Class")
print("=" * 60)

# Import the config module
try:
    # Import the module directly to avoid any caching issues
    import casebuilder.core.config as config_module
    importlib.reload(config_module)
    
    print("✅ Successfully imported config module")
    print(f"Module path: {config_module.__file__}")
    
    # Print the source code of the Settings class
    print("\n📄 Settings class source:")
    print("-" * 60)
    print(inspect.getsource(config_module.Settings))
    print("-" * 60)
    
    # Try to create an instance of Settings
    print("\n🔄 Creating Settings instance...")
    try:
        settings = config_module.Settings()
        print("✅ Successfully created Settings instance")
        print(f"  - CORS_ORIGINS: {settings.CORS_ORIGINS}")
        print(f"  - ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"  - DEBUG: {settings.DEBUG}")
    except Exception as e:
        print(f"❌ Error creating Settings instance: {e}")
        print("\n🔍 Detailed error:")
        traceback.print_exc()
        
        # Try to create a minimal Settings class
        print("\n🔄 Testing with minimal Settings class...")
        try:
            from pydantic_settings import BaseSettings
            
            class MinimalSettings(BaseSettings):
                CORS_ORIGINS: str = "*"
                ENVIRONMENT: str = "development"
                DEBUG: bool = True
            
            print("✅ Created minimal Settings class")
            
            minimal_settings = MinimalSettings()
            print("✅ Successfully created minimal Settings instance")
            print(f"  - CORS_ORIGINS: {minimal_settings.CORS_ORIGINS}")
            print(f"  - ENVIRONMENT: {minimal_settings.ENVIRONMENT}")
            print(f"  - DEBUG: {minimal_settings.DEBUG}")
            
        except Exception as e2:
            print(f"❌ Error with minimal Settings class: {e2}")
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error importing config module: {e}")
    traceback.print_exc()

print("\n🏁 Test completed!")
