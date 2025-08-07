"""
Script to test Python environment and basic imports.
"""
import sys
import os
import platform
import importlib
from pathlib import Path

print("=" * 60)
print("🐍 Python Environment Test")
print("=" * 60)

# Basic Python info
print("\n📋 Python Version:")
print(f"Python {sys.version}")
print(f"Executable: {sys.executable}")
print(f"Platform: {platform.platform()}")

# Environment variables
print("\n📋 Environment Variables:")
for var in ["PATH", "PYTHONPATH", "VIRTUAL_ENV"]:
    print(f"{var}: {os.environ.get(var, 'Not set')}")

# Check working directory
print("\n📋 Working Directory:")
print(f"Current: {os.getcwd()}")
print(f"Script: {Path(__file__).resolve()}")

# Check Python path
print("\n📋 Python Path:")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

# Test basic imports
print("\n🔍 Testing Imports:")
for module in ["pydantic", "fastapi", "sqlalchemy", "uvicorn"]:
    try:
        mod = importlib.import_module(module)
        print(f"✅ {module}: {mod.__file__}")
    except ImportError as e:
        print(f"❌ {module}: {e}")

# Test file operations
try:
    print("\n📝 Testing file operations...")
    test_file = Path("test_file.txt")
    test_file.write_text("test")
    print(f"✅ Wrote to {test_file}")
    
    if test_file.read_text() == "test":
        print("✅ Read from file successful")
    else:
        print("❌ Read from file failed")
    
    test_file.unlink()
    print("✅ File deleted")
except Exception as e:
    print(f"❌ File operation test failed: {e}")

print("\n🏁 Test completed!")
