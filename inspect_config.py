"""
Script to inspect the configuration module directly.
"""
import os
import sys
import importlib.util
from pathlib import Path

def load_module(module_path, module_name):
    """Load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Set environment variables for testing
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["SQLITE_DB"] = "sqlite:///./test_fileboss.db"
os.environ["DATABASE_URL"] = os.environ["SQLITE_DB"]

# Get the path to the config module
project_root = Path(__file__).resolve().parent
config_path = project_root / "casebuilder" / "core" / "config.py"

print(f"🔍 Inspecting config at: {config_path}")

# Print the content of the config file
print("\n📄 Config file content:")
print("=" * 80)
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        print(f.read())
except Exception as e:
    print(f"❌ Error reading config file: {e}")
print("=" * 80)

# Try to load the module directly
try:
    print("\n🔄 Attempting to load config module...")
    config = load_module(config_path, "casebuilder.core.config")
    print("✅ Successfully loaded config module")
    
    # Try to access settings
    try:
        settings = config.settings
        print("✅ Successfully accessed settings")
        print(f"📋 ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"📋 DEBUG: {settings.DEBUG}")
        print(f"📋 CORS_ORIGINS: {settings.CORS_ORIGINS}")
    except Exception as e:
        print(f"❌ Error accessing settings: {e}")
        
        # Try to create a new settings instance
        try:
            print("\n🔄 Trying to create a new Settings instance...")
            settings = config.Settings()
            print("✅ Successfully created new Settings instance")
            print(f"📋 ENVIRONMENT: {settings.ENVIRONMENT}")
            print(f"📋 DEBUG: {settings.DEBUG}")
            print(f"📋 CORS_ORIGINS: {settings.CORS_ORIGINS}")
        except Exception as e2:
            print(f"❌ Error creating Settings instance: {e2}")
            print("\n🔍 Detailed error:")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"❌ Error loading config module: {e}")
    print("\n🔍 Detailed error:")
    import traceback
    traceback.print_exc()

print("\n🏁 Inspection completed!")
