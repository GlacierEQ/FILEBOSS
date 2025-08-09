""
Auto Organize

Automatically organize files from a source directory into the CaseBuilder system.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auto_organize.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up the Python environment."""
    try:
        import pip
        from watchdog.observers import Observer
        return True
    except ImportError:
        logger.info("Installing required packages...")
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
        except Exception as e:
            logger.error(f"Failed to install requirements: {e}")
            return False

def initialize_database():
    """Initialize the database."""
    try:
        from casebuilder.models.base import init_db
        init_db()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def start_watch_service(source_dir: str, case_id: str):
    """Start the watch service for automatic file organization."""
    try:
        from casebuilder.services.watch_service import WatchService
        from casebuilder.services.database import DatabaseService
        from casebuilder.services.file_organizer import FileOrganizer
        from casebuilder.models import FileCategory
        
        # Initialize services
        db_service = DatabaseService(next(DatabaseService.get_db()))
        organizer = FileOrganizer()
        watch_service = WatchService(db_service=db_service, organizer=organizer)
        
        # Start the service
        watch_service.start()
        
        # Add the source directory as a watch
        watch_service.add_watch(
            directory=source_dir,
            case_id=case_id,
            category=FileCategory.EVIDENCE,
            recursive=True
        )
        
        logger.info(f"Watching directory: {source_dir} (Case: {case_id})")
        logger.info("Press Ctrl+C to stop...")
        
        # Keep the service running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping watch service...")
            watch_service.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"Error in watch service: {e}")
        return False

def main():
    """Main function."""
    # Default values
    source_dir = os.path.join(os.path.expanduser("~"), "CaseFiles")
    case_id = "DEFAULT_CASE"
    
    # Create source directory if it doesn't exist
    os.makedirs(source_dir, exist_ok=True)
    
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║           CaseBuilder Auto Organizer             ║
    ╚══════════════════════════════════════════════════╝
    
    This will automatically organize files from:
    {source_dir}
    
    Files will be organized into case: {case_id}
    
    Just drop files into the CaseFiles folder and they'll be
    automatically processed and organized.
    
    Press Enter to continue or Ctrl+C to exit...
    """)
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return
    
    # Set up environment
    if not setup_environment():
        print("\nFailed to set up the environment. Please check the logs.")
        return
    
    # Initialize database
    if not initialize_database():
        print("\nFailed to initialize the database. Please check the logs.")
        return
    
    # Start the watch service
    print(f"\nStarting automatic organization in: {source_dir}")
    print("Press Ctrl+C at any time to stop.")
    
    start_watch_service(source_dir, case_id)
    
    print("\nThank you for using CaseBuilder Auto Organizer!")

if __name__ == "__main__":
    main()
