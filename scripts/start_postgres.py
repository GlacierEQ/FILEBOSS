"""
Script to help start PostgreSQL server and verify the connection.
"""
import os
import sys
import subprocess
import time
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
logger = logging.getLogger("postgres_helper")

def is_postgres_running():
    """Check if PostgreSQL is running by attempting to connect to it."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432
        )
        conn.close()
        return True
    except Exception as e:
        logger.debug(f"PostgreSQL check failed: {e}")
        return False

def start_postgres_service():
    """Attempt to start the PostgreSQL service."""
    try:
        logger.info("Attempting to start PostgreSQL service...")
        
        # Try different methods to start PostgreSQL on Windows
        methods = [
            # Method 1: Using net start
            ["net", "start", "postgresql-x64-14"],  # Common service name for PostgreSQL 14
            ["net", "start", "postgresql-x64-13"],  # Common service name for PostgreSQL 13
            ["net", "start", "postgresql-x64-12"],  # Common service name for PostgreSQL 12
            ["net", "start", "postgresql"],        # Generic service name
            
            # Method 2: Using pg_ctl (if in PATH)
            ["pg_ctl", "start", "-D", "C:\\Program Files\\PostgreSQL\\14\\data"],  # Common path for PostgreSQL 14
            ["pg_ctl", "start", "-D", "C:\\Program Files\\PostgreSQL\\13\\data"],  # Common path for PostgreSQL 13
            ["pg_ctl", "start", "-D", "C:\\Program Files\\PostgreSQL\\12\\data"],  # Common path for PostgreSQL 12
        ]
        
        for cmd in methods:
            try:
                logger.info(f"Trying: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info(f"Success: {result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                logger.debug(f"Command failed: {e.stderr}")
                continue
                
        logger.error("Failed to start PostgreSQL using common methods.")
        return False
        
    except Exception as e:
        logger.error(f"Error starting PostgreSQL: {e}")
        return False

def setup_environment():
    """Set up the environment for database operations."""
    # Add the project root to the Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Set default environment variables if not already set
    os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fileboss")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("POSTGRES_USER", "postgres")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
    os.environ.setdefault("POSTGRES_DB", "fileboss")

def main():
    """Main function to handle PostgreSQL server startup and verification."""
    logger.info("=" * 80)
    logger.info("POSTGRESQL SERVER SETUP")
    logger.info("=" * 80)
    
    # Set up environment
    setup_environment()
    
    # Check if PostgreSQL is already running
    if is_postgres_running():
        logger.info("✅ PostgreSQL is already running!")
        return True
    
    logger.warning("PostgreSQL is not running. Attempting to start...")
    
    # Try to start PostgreSQL
    if start_postgres_service():
        # Give it a moment to start
        logger.info("Waiting for PostgreSQL to start...")
        time.sleep(5)
        
        # Verify it's running
        if is_postgres_running():
            logger.info("✅ Successfully started PostgreSQL!")
            return True
        else:
            logger.error("❌ PostgreSQL service started but not responding.")
    else:
        logger.error("❌ Failed to start PostgreSQL service.")
    
    # Provide manual instructions
    logger.info("\nMANUAL INSTRUCTIONS:")
    logger.info("1. Open 'Services' application (press Win+R, type 'services.msc', press Enter)")
    logger.info("2. Find 'postgresql' service")
    logger.info("3. Right-click and select 'Start'")
    logger.info("4. Make sure the service is set to 'Automatic' startup type")
    logger.info("\nAlternatively, you can start it from command prompt as administrator:")
    logger.info("  net start postgresql-x64-14")
    
    return False

if __name__ == "__main__":
    if main():
        logger.info("✅ PostgreSQL setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ PostgreSQL setup failed!")
        sys.exit(1)
