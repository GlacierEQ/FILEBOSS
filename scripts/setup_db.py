"""
Database setup and verification script.
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
logger = logging.getLogger("db_setup")

def setup_environment():
    """Set up the environment for database operations."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Set default database URL if not already set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/fileboss"
        logger.info(f"Set default DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    # Log environment information
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")

def test_database_connection():
    """Test the database connection with the current configuration."""
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        db_url = os.environ["DATABASE_URL"]
        logger.info(f"Testing connection to: {db_url}")
        
        # Create engine with echo=True for detailed logging
        engine = create_engine(db_url, echo=True)
        
        # Test connection
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Connected to database: {version}")
            
            # Check if database exists
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"Current database: {db_name}")
            
            return True
            
    except ImportError as e:
        logger.error(f"❌ Failed to import required modules: {e}")
        return False
    except SQLAlchemyError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        return False

def create_database():
    """Create the database if it doesn't exist."""
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        # Connect to the default 'postgres' database to create our database
        db_url = os.environ["DATABASE_URL"]
        base_url = "/".join(db_url.split("/")[:-1])  # Remove the database name
        
        logger.info(f"Connecting to: {base_url}")
        engine = create_engine(f"{base_url}/postgres")
        
        # Get the database name from the URL
        db_name = db_url.split("/")[-1].split("?")[0]
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name}
            )
            
            if not result.scalar():
                # Create the database
                logger.info(f"Creating database: {db_name}")
                conn.execute(text(f"COMMIT"))  # End any open transaction
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"✅ Created database: {db_name}")
            else:
                logger.info(f"✅ Database already exists: {db_name}")
                
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        return False

def main():
    """Main function to set up and test the database."""
    logger.info("Starting database setup...")
    
    # Set up environment
    setup_environment()
    
    # Create database if it doesn't exist
    if not create_database():
        logger.error("❌ Failed to set up database")
        return False
    
    # Test database connection
    if not test_database_connection():
        logger.error("❌ Database connection test failed")
        return False
    
    logger.info("✅ Database setup completed successfully!")
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
