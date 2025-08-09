"""
Script to inspect the database schema and verify tables.
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
logger = logging.getLogger("db_inspect")

def inspect_database():
    """Inspect the database schema and verify tables."""
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Import required modules
        from sqlalchemy import inspect, create_engine
        from app.core.config import settings
        
        logger.info(f"Connecting to database: {settings.SQLALCHEMY_DATABASE_URI}")
        
        # Create engine
        engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        
        # Create inspector
        inspector = inspect(engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        
        if not tables:
            logger.warning("No tables found in the database!")
            return False
            
        logger.info(f"Found {len(tables)} tables in the database:")
        
        # Display table details
        for table_name in sorted(tables):
            logger.info(f"\nTable: {table_name}")
            logger.info("-" * (len(table_name) + 8))
            
            # Get columns
            columns = inspector.get_columns(table_name)
            logger.info("Columns:")
            for col in columns:
                logger.info(f"  - {col['name']}: {col['type']}")
                
            # Get primary keys
            pks = inspector.get_pk_constraint(table_name)
            if pks['constrained_columns']:
                logger.info(f"Primary Key: {', '.join(pks['constrained_columns'])}")
                
            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                logger.info("Foreign Keys:")
                for fk in fks:
                    logger.info(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to inspect database: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting database inspection...")
    if inspect_database():
        logger.info("✅ Database inspection completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Database inspection failed!")
        sys.exit(1)
