"""
Debug script to gather comprehensive environment and configuration information.
"""
import os
import sys
import platform
import importlib
import traceback
from pathlib import Path

def print_header(title):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"🔍 {title}")
    print(f"{'=' * 60}")

def get_package_version(package_name):
    """Get the version of an installed package."""
    try:
        return importlib.import_module(package_name).__version__
    except (ImportError, AttributeError):
        try:
            import pkg_resources
            return pkg_resources.get_distribution(package_name).version
        except:
            return "Not installed or version not available"

def main():
    # Basic system information
    print_header("System Information")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Executable: {sys.executable}")
    
    # Environment variables
    print_header("Environment Variables")
    for var in ["PATH", "PYTHONPATH", "VIRTUAL_ENV", "CORS_ORIGINS", "ENVIRONMENT", "DEBUG"]:
        print(f"{var}: {os.environ.get(var, 'Not set')}")
    
    # Python path
    print_header("Python Path")
    for i, path in enumerate(sys.path):
        print(f"{i}: {path}")
    
    # Package versions
    print_header("Package Versions")
    packages = ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "pydantic-settings"]
    for pkg in packages:
        print(f"{pkg}: {get_package_version(pkg)}")
    
    # Test project imports
    print_header("Project Import Test")
    
    # Add project root to path if needed
    project_root = str(Path(__file__).resolve().parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Test config import
    print("\nTesting config import...")
    try:
        from casebuilder.core.config import Settings
        print("✅ Successfully imported Settings from config")
        
        # Try to create a settings instance
        try:
            settings = Settings()
            print("✅ Successfully created Settings instance")
            print(f"  - CORS_ORIGINS: {settings.CORS_ORIGINS}")
            print(f"  - ENVIRONMENT: {settings.ENVIRONMENT}")
            print(f"  - DEBUG: {settings.DEBUG}")
        except Exception as e:
            print(f"❌ Error creating Settings instance: {e}")
            traceback.print_exc()
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        traceback.print_exc()
    
    # Test database connection
    print("\nTesting database connection...")
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
        traceback.print_exc()
    
    # Test FastAPI app
    print("\nTesting FastAPI app...")
    try:
        from casebuilder.api.app import app
        print("✅ Successfully imported FastAPI app")
        
        # Test app routes
        routes = [f"{route.path} ({', '.join(route.methods)})" for route in app.routes]
        print(f"  - Available routes: {routes[:5]}..." if len(routes) > 5 else f"  - Available routes: {routes}")
        
    except Exception as e:
        print(f"❌ Error importing FastAPI app: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
    print("\n🏁 Debug script completed!")
