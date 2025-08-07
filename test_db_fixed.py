"""
Test script to verify database initialization and basic operations.
"""
import asyncio
import os
import sys
from pathlib import Path

# Set environment variable for CORS_ORIGINS before importing any app code
os.environ["CORS_ORIGINS"] = "*"

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from casebuilder.db.base import init_db, engine, async_engine
from casebuilder.db.models import Base
from casebuilder.core.config import settings

async def test_database_connection() -> None:
    """Test the database connection and table creation."""
    print("Testing database connection...")
    
    # Initialize the database
    print("Initializing database...")
    init_db()
    
    # Check if tables were created
    print("\nChecking database tables:")
    async with async_engine.connect() as conn:
        result = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"Found tables: {', '.join(tables) if tables else 'No tables found'}")
    
    print("\nDatabase test completed successfully!")

if __name__ == "__main__":
    print(f"Using database: {settings.DATABASE_URI}")
    asyncio.run(test_database_connection())
