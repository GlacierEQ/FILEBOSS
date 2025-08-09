"""
Script to verify that all required imports are working correctly.
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

def check_imports() -> bool:
    """Check that all required imports are working.
    
    Returns:
        bool: True if all imports are successful, False otherwise
    """
    try:
        # Add the project root to the Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        logger.info(f"Added to Python path: {project_root}")
        
        # Try importing core modules
        try:
            import app.core.config
            logger.info("✅ Successfully imported app.core.config")
        except ImportError as e:
            logger.error(f"❌ Failed to import app.core.config: {e}")
            return False
            
        try:
            from app.db.session import engine
            logger.info("✅ Successfully imported app.db.session")
        except ImportError as e:
            logger.error(f"❌ Failed to import app.db.session: {e}")
            return False
            
        try:
            import sqlalchemy
            logger.info(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
        except ImportError as e:
            logger.error(f"❌ Failed to import SQLAlchemy: {e}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Starting import checks...")
    if check_imports():
        logger.info("✅ All imports are working correctly!")
        sys.exit(0)
    else:
        logger.error("❌ Some imports failed. Please check the logs above for details.")
        sys.exit(1)
