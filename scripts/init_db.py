#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the database, creates tables, and runs migrations.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "logs" / "database.log")
    ]
)
logger = logging.getLogger(__name__)

# Import after path configuration
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.db.session import engine, Base, init_db, session_scope
from app.core.config import settings

# Constants
ALEMBIC_INI = project_root / "alembic.ini"
ALEMBIC_DIR = project_root / "alembic"


def ensure_logs_directory() -> None:
    """Ensure the logs directory exists."""
    logs_dir = project_root / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)


def run_migrations() -> None:
    """Run database migrations using Alembic."""
    logger.info("Running database migrations...")
    
    try:
        # Ensure we're using the correct working directory
        os.chdir(str(project_root))
        
        # Configure Alembic
        if not ALEMBIC_INI.exists():
            raise FileNotFoundError(f"Alembic config file not found at {ALEMBIC_INI}")
            
        alembic_cfg = Config(str(ALEMBIC_INI))
        
        # Set the database URL in the Alembic config
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))
        
        # Ensure migrations directory exists
        if not ALEMBIC_DIR.exists():
            logger.info("Initializing new Alembic migrations")
            command.init(alembic_cfg, str(ALEMBIC_DIR))
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to run database migrations: {str(e)}", exc_info=True)
        raise


async def create_tables() -> None:
    """Create database tables if they don't exist."""
    logger.info("Creating database tables...")
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
        # Initialize the database with default data
        init_db()
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
        raise


def check_database_connection(retries: int = 3, delay: int = 2) -> bool:
    """
    Check if the database is accessible.
    
    Args:
        retries: Number of connection retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        bool: True if connection is successful, False otherwise
    """
    import time
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempting to connect to the database (Attempt {attempt}/{retries})...")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database")
            return True
            
        except Exception as e:
            if attempt == retries:
                logger.error(f"Failed to connect to the database after {retries} attempts: {str(e)}", 
                           exc_info=True)
                return False
                
            logger.warning(f"Connection attempt {attempt} failed: {str(e)}. Retrying in {delay} seconds...")
            time.sleep(delay)
    
    return False


async def main() -> None:
    """Main function to initialize the database."""
    try:
        ensure_logs_directory()
        logger.info("Starting database initialization...")
        
        # Check database connection
        if not check_database_connection():
            logger.error("Could not connect to the database. Please check your database configuration.")
            sys.exit(1)
        
        # Create tables and initialize data
        await create_tables()
        
        # Run migrations
        run_migrations()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
    
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
