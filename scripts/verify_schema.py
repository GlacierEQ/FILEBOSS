"""
Enhanced script to verify database schema with detailed logging.
"""
import os
import sys
import logging
from pathlib import Path

# Set up logging to both console and file
log_file = Path("schema_verification.log")
log_file.unlink(missing_ok=True)  # Remove previous log file if it exists

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode='w')
    ]
)
logger = logging.getLogger("schema_verify")

def verify_schema():
    """Verify the database schema with detailed logging."""
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Import required modules
        from sqlalchemy import inspect, create_engine, text
        from app.core.config import settings
        
        logger.info("=" * 80)
        logger.info("DATABASE SCHEMA VERIFICATION")
        logger.info("=" * 80)
        
        # Log database connection info
        logger.info(f"Database URL: {settings.SQLALCHEMY_DATABASE_URI}")
        
        # Create engine with echo=True for detailed SQL logging
        engine = create_engine(
            str(settings.SQLALCHEMY_DATABASE_URI),
            echo=True
        )
        
        # Create inspector
        inspector = inspect(engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        
        if not tables:
            logger.error("❌ No tables found in the database!")
            return False
            
        logger.info(f"\nFound {len(tables)} tables in the database:")
        logger.info("-" * 40)
        
        # Expected tables based on our models
        expected_tables = {
            'alembic_version',  # Added by Alembic
            'users',
            'permissions',
            'files',
            'directories',
            'user_permissions'  # For many-to-many relationship
        }
        
        # Check for missing tables
        missing_tables = expected_tables - set(tables)
        if missing_tables:
            logger.warning(f"⚠️  Missing tables: {', '.join(sorted(missing_tables))}")
        
        # Verify each table
        for table_name in sorted(tables):
            logger.info(f"\n🔍 Table: {table_name}")
            logger.info("-" * (len(table_name) + 10))
            
            # Get columns
            columns = inspector.get_columns(table_name)
            logger.info(f"Columns ({len(columns)}):")
            for col in columns:
                nullable = "NULL" if col.get("nullable") else "NOT NULL"
                default = f" DEFAULT {col.get('default')}" if col.get("default") is not None else ""
                logger.info(f"  - {col['name']}: {col['type']} {nullable}{default}")
                
            # Get primary keys
            try:
                pks = inspector.get_pk_constraint(table_name)
                if pks and pks.get('constrained_columns'):
                    logger.info(f"Primary Key: {', '.join(pks['constrained_columns'])}")
            except Exception as e:
                logger.warning(f"  Could not get primary key info: {e}")
                
            # Get foreign keys
            try:
                fks = inspector.get_foreign_keys(table_name)
                if fks:
                    logger.info("Foreign Keys:")
                    for fk in fks:
                        on_delete = f" ON DELETE {fk.get('ondelete', 'NO ACTION')}" 
                        on_update = f" ON UPDATE {fk.get('onupdate', 'NO ACTION')}" 
                        logger.info(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}{on_delete}{on_update}")
            except Exception as e:
                logger.warning(f"  Could not get foreign key info: {e}")
                
            # Get indexes
            try:
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    logger.info("Indexes:")
                    for idx in indexes:
                        unique = "UNIQUE " if idx.get('unique') else ""
                        logger.info(f"  - {unique}INDEX {idx.get('name')}: {', '.join(idx.get('column_names', []))}")
            except Exception as e:
                logger.warning(f"  Could not get index info: {e}")
        
        # Check if all expected tables are present
        if missing_tables:
            logger.error(f"❌ Verification failed: Missing {len(missing_tables)} tables")
            return False
            
        logger.info("\n✅ Database schema verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ An error occurred during schema verification: {e}", exc_info=True)
        return False
    finally:
        logger.info(f"\nLog saved to: {log_file.absolute()}")

if __name__ == "__main__":
    logger.info("Starting database schema verification...")
    if verify_schema():
        logger.info("✅ Verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Verification failed! Check the log file for details.")
        sys.exit(1)
