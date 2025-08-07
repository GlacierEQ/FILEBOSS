"""
Simplified test script to verify basic Python environment and imports.
"""
import sys
import os
from pathlib import Path

print("🐍 Python version:", sys.version)
print("📁 Current working directory:", os.getcwd())
print("📦 Python path:", sys.path)

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
print("\n📂 Project root:", project_root)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("✅ Added project root to Python path")

# Try to import the settings module
try:
    print("\n🔍 Attempting to import settings...")
    from casebuilder.core import config
    print("✅ Successfully imported casebuilder.core.config")
    
    # Print the module's file location
    print(f"📄 Config module location: {config.__file__}")
    
    # Try to access settings
    try:
        settings = config.settings
        print("✅ Successfully accessed settings")
        print(f"📋 ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"📋 DEBUG: {settings.DEBUG}")
        print(f"📋 CORS_ORIGINS: {settings.CORS_ORIGINS}")
    except Exception as e:
        print(f"❌ Error accessing settings: {e}")
        
except Exception as e:
    print(f"❌ Error importing config: {e}")
    import traceback
    traceback.print_exc()

# Test basic file operations
print("\n📝 Testing file operations...")
test_file = Path("test_file.txt")
try:
    test_file.write_text("test")
    print(f"✅ Successfully wrote to {test_file}")
    test_file.unlink()
    print(f"✅ Successfully deleted {test_file}")
except Exception as e:
    print(f"❌ File operation test failed: {e}")

print("\n🏁 Test completed!")
