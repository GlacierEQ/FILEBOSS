#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database and runs migrations.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from casebuilder.db.session import Base, engine, init_db
from casebuilder.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALEMBIC_INI = "alembic.ini"
ALEMBIC_DIR = "alembic"

def run_migrations() -> None:
    """Run database migrations."""
    logger.info("Running database migrations...")
    
    # Ensure we're using the correct working directory
    os.chdir(str(Path(__file__).parent.parent))
    
    # Configure Alembic
    alembic_cfg = Config(ALEMBIC_INI)
    
    # Set the database URL in the Alembic config
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URI))
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations completed")

async def create_tables() -> None:
    """Create database tables."""
    logger.info("Creating database tables...")
    
    # Import models to ensure they are registered with SQLAlchemy
    from casebuilder import models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")

async def check_database_connection() -> bool:
    """Check if the database is accessible."""
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Successfully connected to the database")
                return True
        except Exception as e:
            if attempt < max_retries:
                logger.warning(
                    f"Database connection attempt {attempt} failed: {e}. "
                    f"Retrying in {retry_delay} seconds..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to connect to the database after multiple attempts")
                return False
    return False

async def main() -> None:
    """Main function to initialize the database."""
    logger.info("Starting database initialization...")
    
    # Check database connection
    if not await check_database_connection():
        logger.error("Failed to connect to the database. Exiting...")
        sys.exit(1)
    
    # Create tables if they don't exist
    await create_tables()
    
    # Run migrations
    run_migrations()
    
    logger.info("Database initialization completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
