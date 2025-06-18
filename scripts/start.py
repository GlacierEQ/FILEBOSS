#!/usr/bin/env python3
"""
Application Entry Point

This script is the main entry point for running the CaseBuilder application.
"""
import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from casebuilder.api.app import app as fastapi_app
from casebuilder.core.config import settings
from casebuilder.db.session import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)
app.mount("/", fastapi_app)

# Handle graceful shutdown
async def shutdown_event():
    """Handle application shutdown."""
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")

def handle_sigterm(*args):
    """Handle SIGTERM signal."""
    logger.info("Received SIGTERM. Starting graceful shutdown...")
    raise KeyboardInterrupt()

async def init_application():
    """Initialize the application."""
    logger.info("Starting application initialization...")
    
    # Initialize database
    await init_db()
    
    # Register shutdown handler
    app.add_event_handler("shutdown", shutdown_event)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    logger.info("Application initialization complete")

def run():
    """Run the application."""
    # Run initialization
    asyncio.run(init_application())
    
    # Start the server
    uvicorn.run(
        "scripts.start:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=logging.getLevelName(logging.INFO).lower(),
        workers=settings.WORKERS,
    )

if __name__ == "__main__":
    run()
