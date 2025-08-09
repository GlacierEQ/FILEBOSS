"""
Script to run database migrations using Alembic.
"""
import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("migrations")

def run_migrations():
    """Run database migrations using Alembic."""
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Set environment variable for Alembic
        os.environ["PYTHONPATH"] = str(project_root)
        
        # Import settings to ensure environment variables are loaded
        from app.core.config import settings
        
        # Set the database URL for Alembic
        os.environ["SQLALCHEMY_DATABASE_URI"] = str(settings.SQLALCHEMY_DATABASE_URI)
        
        logger.info(f"Running migrations for database: {settings.SQLALCHEMY_DATABASE_URI}")
        
        # Import Alembic
        from alembic.config import Config
        from alembic import command
        
        # Get the path to the alembic.ini file
        alembic_cfg = Config("alembic.ini")
        
        # Run the upgrade command
        logger.info("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        
        # Verify the migration
        logger.info("Verifying migration...")
        from app.db.session import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        
        logger.info("✅ Database migrations completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to run migrations: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting database migration process...")
    if run_migrations():
        logger.info("✅ Migration process completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Migration process failed!")
        sys.exit(1)
