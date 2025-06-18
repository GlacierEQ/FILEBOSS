#!/usr/bin/env python3
"""
Create Database Migration

This script creates a new database migration using Alembic.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_migration(message: str = None, autogenerate: bool = True) -> None:
    """Create a new database migration.
    
    Args:
        message: Migration message
        autogenerate: Whether to autogenerate the migration
    """
    # Ensure we're using the correct working directory
    os.chdir(str(Path(__file__).parent.parent))
    
    # Configure Alembic
    alembic_cfg = Config("alembic.ini")
    
    # Create the migration
    try:
        command.revision(
            config=alembic_cfg,
            message=message,
            autogenerate=autogenerate,
            rev_id=None,
            version_path=None,
            branch_label=None,
            splice=False,
            head="head",
            depends_on=None,
        )
        logger.info("Migration created successfully")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        sys.exit(1)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Create a new database migration")
    parser.add_argument(
        "-m", "--message",
        type=str,
        required=True,
        help="Migration message"
    )
    parser.add_argument(
        "--no-autogenerate",
        action="store_false",
        dest="autogenerate",
        help="Create an empty migration without autogenerating changes"
    )
    
    args = parser.parse_args()
    create_migration(args.message, args.autogenerate)

if __name__ == "__main__":
    main()
