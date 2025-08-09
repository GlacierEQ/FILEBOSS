"""Alembic environment configuration.

This module is used by Alembic to run database migrations.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import application modules after path configuration
from app.core.config import settings
from app.db.session import Base
from app.models import *  # noqa: F401, F403 - Import all models for migration

# Alembic Config object, which provides access to the values within the .ini file
config = context.config

# Set up Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set up logging for Alembic
logger = logging.getLogger('alembic')

# Get the metadata from the base class for use in migrations
target_metadata = Base.metadata

def get_database_url() -> str:
    """Get the database URL from settings.
    
    Returns:
        str: The database URL
    """
    return str(settings.SQLALCHEMY_DATABASE_URI)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    By skipping the Engine creation, we don't need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    """
    # Get the database URL from settings
    url = get_database_url()
    
    # Create a connection pool with settings from our configuration
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=url,
    )

    # Connect to the database and run migrations
    with connectable.connect() as connection:
        logger.info(f"Running migrations against database: {url}")
        
        # Configure the context with the connection and metadata
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # Enable the following for better autogenerate support
            # render_as_batch=True,  # For SQLite compatibility
            # process_revision_directives=process_revision_directives,
        )

        # Run migrations within a transaction
        with context.begin_transaction():
            context.run_migrations()


if __name__ == "__main__":
    # When running as a script, use the appropriate migration function
    if context.is_offline_mode():
        logger.info("Running migrations in OFFLINE mode")
        run_migrations_offline()
    else:
        logger.info("Running migrations in ONLINE mode")
        run_migrations_online()

    logger.info("Migrations completed successfully")
else:
    # When imported as a module, just set up the configuration
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()

