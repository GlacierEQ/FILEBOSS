"""
Script to verify database connection with detailed logging.
"""
import os
import sys
import logging
from pathlib import Path

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def verify_database_connection() -> bool:
    """Verify the database connection with detailed logging.
    
    Returns:
        bool: True if connection was successful, False otherwise
    """
    try:
        logger.info("Starting database verification...")
        
        # Import settings with error handling
        try:
            from app.core.config import settings
            logger.info("Successfully imported application settings")
        except ImportError as e:
            logger.error(f"Failed to import settings: {e}")
            return False
            
        # Log database configuration
        logger.info("Database configuration:")
        logger.info(f"  - Server: {settings.POSTGRES_SERVER}")
        logger.info(f"  - Database: {settings.POSTGRES_DB}")
        logger.info(f"  - User: {settings.POSTGRES_USER}")
        logger.info(f"  - Full URL: {settings.SQLALCHEMY_DATABASE_URI}")
        
        # Test SQLAlchemy connection
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.exc import SQLAlchemyError
            
            # Create a new engine with echo=True for debugging
            test_engine = create_engine(
                str(settings.SQLALCHEMY_DATABASE_URI),
                echo=True,
                pool_pre_ping=True
            )
            
            logger.info("Attempting to connect to the database...")
            with test_engine.connect() as connection:
                # Test connection with a simple query
                result = connection.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✅ Successfully connected to the database!")
                logger.info(f"Database version: {version}")
                
                # Verify the database exists and is accessible
                result = connection.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                logger.info(f"Connected to database: {db_name}")
                
                # List all tables in the database
                result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                logger.info(f"Tables in database: {tables}")
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if verify_database_connection():
        sys.exit(0)
    else:
        sys.exit(1)
