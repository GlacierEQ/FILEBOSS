"""
Test script to verify database connection with detailed error reporting.
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

def test_connection() -> bool:
    """Test the database connection with detailed error reporting.
    
    Returns:
        bool: True if connection was successful, False otherwise
    """
    try:
        logger.info("Starting database connection test...")
        
        # Import settings and engine with error handling
        try:
            from app.core.config import settings
            from app.db.session import engine
            logger.info("Successfully imported application modules")
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            logger.error("Please ensure the application is properly installed and all dependencies are available")
            return False
            
        # Log database configuration
        logger.info(f"Database configuration:")
        logger.info(f"  - Server: {settings.POSTGRES_SERVER}")
        logger.info(f"  - Database: {settings.POSTGRES_DB}")
        logger.info(f"  - User: {settings.POSTGRES_USER}")
        logger.info(f"  - Full URL: {settings.SQLALCHEMY_DATABASE_URI}")
        
        # Test the connection
        try:
            logger.info("Attempting to establish database connection...")
            with engine.connect() as connection:
                # Execute a simple query to verify the connection
                result = connection.execute("SELECT version();")
                version = result.scalar()
                logger.info(f"✅ Successfully connected to the database!")
                logger.info(f"Database version: {version}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to the database: {str(e)}")
            logger.error("Please check the following:")
            logger.error("1. Is the database server running?")
            logger.error("2. Are the connection details in your .env file correct?")
            logger.error(f"3. Can you connect to {settings.POSTGRES_SERVER} on port 5432?")
            return False
            
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_connection():
        sys.exit(0)
    else:
        sys.exit(1)
