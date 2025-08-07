"""
Test script to verify configuration loading.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set environment variables for testing
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"
os.environ["SQLITE_DB"] = "sqlite:///./test_fileboss.db"
os.environ["DATABASE_URL"] = os.environ["SQLITE_DB"]

# Now import the settings
try:
    from casebuilder.core.config import settings
    
    print("✅ Successfully loaded settings!")
    print(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    # Test database connection
    from casebuilder.db.base import Base, engine
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    print("\n✅ Database connection successful!")
    print(f"Tables in database: {inspector.get_table_names()}")
    
except Exception as e:
    print(f"\n❌ Error loading configuration: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
