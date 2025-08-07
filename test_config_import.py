"""
Test script to check basic config module import and settings.
"""
import os
import sys
from pathlib import Path

# Set environment variables
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"

# Add project root to Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("🔍 Testing config module import...")

try:
    # Import the config module
    import casebuilder.core.config as config
    print("✅ Successfully imported config module")
    
    # Print the module's file location
    print(f"📄 Config module location: {config.__file__}")
    
    # Try to access the Settings class
    print("\n🔍 Checking Settings class...")
    if hasattr(config, 'Settings'):
        print("✅ Found Settings class in config module")
        
        # Print the source code of the Settings class
        print("\n📄 Settings class source:")
        print("=" * 80)
        print(inspect.getsource(config.Settings))
        print("=" * 80)
        
        # Try to create an instance
        print("\n🔄 Attempting to create Settings instance...")
        try:
            settings = config.Settings()
            print("✅ Successfully created Settings instance")
            print(f"📋 CORS_ORIGINS: {settings.CORS_ORIGINS}")
            print(f"📋 ENVIRONMENT: {settings.ENVIRONMENT}")
            print(f"📋 DEBUG: {settings.DEBUG}")
        except Exception as e:
            print(f"❌ Error creating Settings instance: {e}")
            print("\n🔍 Detailed error:")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Settings class not found in config module")
        
except ImportError as e:
    print(f"❌ Error importing config module: {e}")
    print("\n🔍 Detailed error:")
    import traceback
    traceback.print_exc()

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("\n🔍 Detailed error:")
    import traceback
    traceback.print_exc()

print("\n🏁 Test completed!")
