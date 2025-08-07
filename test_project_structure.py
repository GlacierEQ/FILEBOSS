"""
Test script to verify project structure and imports.
"""
import os
import sys
from pathlib import Path
import importlib

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🔍 Testing Project Structure and Imports")
print("=" * 60)
print(f"Project Root: {project_root}")
print(f"Python Path: {sys.path}\n")

# Set up environment variables for testing
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"

# Test imports
try:
    # Test importing config
    print("🔍 Testing config import...")
    from casebuilder.core.config import Settings
    print("✅ Successfully imported Settings from config")
    
    # Test creating a settings instance
    print("\n🔍 Testing Settings instantiation...")
    try:
        settings = Settings()
        print("✅ Successfully created Settings instance")
        print(f"  - CORS_ORIGINS: {settings.CORS_ORIGINS}")
        print(f"  - ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"  - DEBUG: {settings.DEBUG}")
    except Exception as e:
        print(f"❌ Error creating Settings instance: {e}")
        import traceback
        traceback.print_exc()
    
    # Test database connection
    print("\n🔍 Testing database connection...")
    try:
        from casebuilder.db.base import Base, engine
        from sqlalchemy import inspect
        
        print("✅ Successfully imported database modules")
        
        # Test database connection
        inspector = inspect(engine)
        print("✅ Successfully connected to database")
        print(f"  - Tables: {inspector.get_table_names()}")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test FastAPI app
    print("\n🔍 Testing FastAPI app...")
    try:
        from casebuilder.api.app import app
        print("✅ Successfully imported FastAPI app")
        
        # Test app routes
        routes = [f"{route.path} ({', '.join(route.methods)})" for route in app.routes]
        print(f"  - Available routes: {routes}")
        
    except Exception as e:
        print(f"❌ Error importing FastAPI app: {e}")
        import traceback
        traceback.print_exc()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Test completed!")
