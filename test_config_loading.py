"""
Test script to verify project configuration loading.
"""
import os
import sys
from pathlib import Path
import importlib
import pkgutil

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🔍 Testing Project Configuration Loading")
print("=" * 60)

# Print environment information
print("\n🔧 Environment Information:")
print(f"Python: {sys.version}")
print(f"Working Directory: {os.getcwd()}")
print(f"Python Path: {sys.path}\n")

# Check for .env file
env_path = Path(".env")
print(f"🔍 Checking for .env file at: {env_path.absolute()}")
if env_path.exists():
    print("✅ .env file exists")
    print("📄 .env file content:")
    print("-" * 40)
    try:
        with open(env_path, 'r') as f:
            print(f.read().strip())
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

# Try to import and test the settings
print("\n🔍 Testing settings import...")
try:
    # Import the config module
    import casebuilder.core.config as config_module
    print("✅ Successfully imported config module")
    
    # Print the module's file location
    print(f"   - Module location: {config_module.__file__}")
    
    # Try to import the Settings class
    try:
        Settings = config_module.Settings
        print("✅ Successfully imported Settings class")
        
        # Try to create an instance of Settings
        print("\n🔄 Creating Settings instance...")
        try:
            settings = Settings()
            print("✅ Successfully created Settings instance")
            
            # Print the settings
            print("\n📋 Current Settings:")
            for attr in dir(settings):
                if not attr.startswith('_') and not callable(getattr(settings, attr)):
                    print(f"   - {attr}: {getattr(settings, attr, 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error creating Settings instance: {e}")
            import traceback
            traceback.print_exc()
    
    except AttributeError as e:
        print(f"❌ Error importing Settings class: {e}")
        
        # Try to find what's available in the module
        print("\n🔍 Available attributes in config module:")
        for name in dir(config_module):
            if not name.startswith('_'):
                print(f"   - {name}: {getattr(config_module, name, 'N/A')}")
    
except ImportError as e:
    print(f"❌ Error importing config module: {e}")
    import traceback
    traceback.print_exc()

# Check for python-dotenv
print("\n🔍 Checking for python-dotenv:")
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv is installed")
    
    # Try loading .env manually
    print("\n🔄 Loading .env file with python-dotenv...")
    dotenv_loaded = load_dotenv(env_path, override=True)
    print(f"   - load_dotenv() returned: {dotenv_loaded}")
    
    # Check environment variables after loading
    print("\n🔍 Environment Variables After dotenv Load:")
    for var in ["CORS_ORIGINS", "ENVIRONMENT", "DEBUG", "DATABASE_URL"]:
        value = os.environ.get(var, "[Not Set]")
        print(f"{var}: {value}")
    
    # Try to create Settings instance again after loading .env
    try:
        from casebuilder.core.config import Settings
        settings = Settings()
        print("\n✅ Successfully created Settings instance after dotenv load")
    except Exception as e:
        print(f"\n❌ Error creating Settings instance after dotenv load: {e}")
        
except ImportError:
    print("❌ python-dotenv is not installed")

print("\n🏁 Configuration test completed!")
