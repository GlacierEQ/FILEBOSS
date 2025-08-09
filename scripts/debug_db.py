"""
Debug script for database connection issues.
"""
import os
import sys
import logging
from pathlib import Path

# Set up basic logging to both console and file
log_file = Path("debug_db.log")
log_file.unlink(missing_ok=True)  # Remove previous log file if it exists

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode='w')
    ]
)
logger = logging.getLogger("debug_db")

def log_environment():
    """Log relevant environment variables."""
    logger.info("Environment variables:")
    for var in ["PYTHONPATH", "DATABASE_URL", "POSTGRES_*"]:
        if var.endswith('*'):
            # Handle wildcard environment variables
            for env_var in os.environ:
                if env_var.startswith(var[:-1]):
                    logger.info(f"  {env_var} = {os.environ[env_var]}")
        else:
            logger.info(f"  {var} = {os.environ.get(var, 'Not set')}")

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection directly."""
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")
        
        # Try different database URLs
        db_urls = [
            os.environ.get("DATABASE_URL"),
            "postgresql://postgres:postgres@localhost:5432/fileboss",
            "postgresql://postgres:postgres@localhost:5432/postgres"
        ]
        
        for db_url in db_urls:
            if not db_url:
                continue
                
            logger.info(f"\nTesting connection to: {db_url}")
            
            try:
                # Create engine with echo=True for detailed logging
                engine = create_engine(db_url, echo=True)
                
                # Test connection
                with engine.connect() as connection:
                    logger.info("✅ Successfully connected to the database!")
                    
                    # Get database version
                    result = connection.execute(text("SELECT version()"))
                    version = result.scalar()
                    logger.info(f"Database version: {version}")
                    
                    # List all databases
                    result = connection.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
                    dbs = [row[0] for row in result]
                    logger.info(f"Available databases: {dbs}")
                    
                    # List all tables in current database
                    if 'fileboss' in db_url:
                        try:
                            result = connection.execute(text("""
                                SELECT table_name 
                                FROM information_schema.tables 
                                WHERE table_schema = 'public'
                            
```python
"""))
                            tables = [row[0] for row in result.fetchall()]
                            logger.info(f"Tables in database: {tables}")
                        except Exception as e:
                            logger.warning(f"Could not list tables: {e}")
                    
                    return True
                    
            except SQLAlchemyError as e:
                logger.error(f"❌ Connection failed: {e}")
                continue
                
        logger.error("❌ All connection attempts failed!")
        return False
        
    except ImportError as e:
        logger.error(f"❌ Failed to import SQLAlchemy: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting database debug script...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Log environment variables
    log_environment()
    
    # Test SQLAlchemy connection
    if test_sqlalchemy_connection():
        logger.info("✅ Database connection test completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Database connection test failed! Check the log file for details.")
        sys.exit(1)
