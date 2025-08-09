"""
Simple script to test SQLAlchemy database connection.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up basic logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection using SQLAlchemy."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        # Get database URL from environment or use default
        db_url = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/fileboss"
        
        logger.info(f"Attempting to connect to database: {db_url}")
        
        # Create engine with echo=True for debugging
        engine = create_engine(db_url, echo=True)
        
        # Test connection
        with engine.connect() as connection:
            # Simple query to test connection
            result = connection.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Successfully connected to the database!")
            logger.info(f"Database version: {version}")
            
            # List all tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            "))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Tables in database: {tables}")
            
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting database connection test...")
    if test_connection():
        logger.info("✅ Database connection test completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Database connection test failed!")
        sys.exit(1)
