#!/usr/bin/env python3
"""
Run the FileBoss application.

This script initializes the database and starts the FastAPI application.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "SECRET_KEY",
        "POSTGRES_SERVER",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please check your .env file and try again.")
        sys.exit(1)

def init_database():
    """Initialize the database with the first superuser."""
    from app.db.session import SessionLocal
    from app.db.init_db import init_db
    
    logger.info("Initializing database...")
    db = SessionLocal()
    try:
        init_db(db)
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)
    finally:
        db.close()

def main():
    """Main entry point for the application."""
    # Check environment variables
    check_environment()
    
    # Initialize database
    init_database()
    
    # Import uvicorn here to avoid loading the app before environment is checked
    import uvicorn
    
    # Start the application
    logger.info("Starting FileBoss application...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
