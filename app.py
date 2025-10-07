#!/usr/bin/env python3
"""FILEBOSS Main Application Entry Point"""

import uvicorn
import logging
from src.sigma_core.main import FileBossCore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("🚀 Starting FILEBOSS - Hyper-Powerful File Manager")
    
    # Initialize core application
    core = FileBossCore()
    app = core.start()
    
    # Start the application
    logger.info("⚡ FILEBOSS is READY for action!")
    
    return app

# Create the FastAPI app instance
app = main()

if __name__ == "__main__":
    # Run with uvicorn if called directly
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )