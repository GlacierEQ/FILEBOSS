"""
Database initialization and migration utilities.
"""
import logging
import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from .base import Base, SessionLocal, async_engine
from ..config import settings

logger = logging.getLogger(__name__)


def setup_database() -> None:
    """Set up the database by creating tables and running migrations."""
    logger.info("Setting up database...")
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.database.url.replace("sqlite:///", "")), exist_ok=True)
    
    # Create tables
    Base.metadata.create_all(bind=async_engine.sync_engine)
    
    # Run migrations
    run_migrations()
    
    logger.info("Database setup complete")


def run_migrations() -> None:
    """Run database migrations using Alembic."""
    logger.info("Running database migrations...")
    
    # Get the directory containing this file
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    
    # If migrations directory doesn't exist, initialize it
    if not os.path.exists(migrations_dir):
        logger.info("Initializing new migrations directory")
        os.makedirs(migrations_dir, exist_ok=True)
        
        # Create a basic alembic.ini file
        alembic_ini = """
        [alembic]
        script_location = %(here)s/migrations
        sqlalchemy.url = %(db_url)s
        
        [loggers]
        keys = root,sqlalchemy,alembic
        
        [handlers]
        keys = console
        
        [formatters]
        keys = generic
        
        [logger_root]
        level = WARN
        handlers = console
        qualname =
        
        [logger_sqlalchemy]
        level = WARN
        handlers =
        qualname = sqlalchemy.engine
        
        [logger_alembic]
        level = INFO
        handlers =
        qualname = alembic
        
        [handler_console]
        class = StreamHandler
        args = (sys.stderr,)
        level = NOTSET
        formatter = generic
        
        [formatter_generic]
        format = %(levelname)-5.5s [%(name)s] %(message)s
        datefmt = %H:%M:%S
        """
        
        # Write the config file
        with open(os.path.join(migrations_dir, "alembic.ini"), "w") as f:
            f.write(alembic_ini)
        
        # Initialize the migrations
        config = Config(os.path.join(migrations_dir, "alembic.ini"))
        config.set_main_option("script_location", migrations_dir)
        config.set_main_option("sqlalchemy.url", settings.database.url)
        
        # Create the initial migration
        command.revision(config, autogenerate=True, message="Initial migration")
    
    # Run migrations
    config = Config(os.path.join(migrations_dir, "alembic.ini"))
    config.set_main_option("script_location", migrations_dir)
    config.set_main_option("sqlalchemy.url", settings.database.url)
    
    # Upgrade to the latest revision
    command.upgrade(config, "head")
    
    logger.info("Migrations complete")


def reset_database() -> None:
    ""
    Drop all tables and recreate them.
    WARNING: This will delete all data in the database!
    """
    if settings.environment != "testing":  # type: ignore
        raise RuntimeError("Cannot reset database in non-testing environment")
    
    logger.warning("Resetting database...")
    
    # Drop all tables
    Base.metadata.drop_all(bind=async_engine.sync_engine)
    
    # Recreate tables
    Base.metadata.create_all(bind=async_engine.sync_engine)
    
    logger.info("Database reset complete")


def check_database_connection() -> bool:
    """Check if the database is accessible."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
            return True
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        setup_database()
