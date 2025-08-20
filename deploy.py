#!/usr/bin/env python3
"""
FILEBOSS Deployment Script

This script handles indexing and deployment of the FILEBOSS project.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    logger.info(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            return False
        logger.info(f"Command output: {result.stdout}")
        return True
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    logger.info("Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        logger.error("Python 3.10+ is required")
        return False
    
    # Check if Docker is available
    if not run_command("docker --version"):
        logger.warning("Docker not available - will use local deployment")
        return "local"
    
    if not run_command("docker-compose --version"):
        logger.warning("Docker Compose not available - will use local deployment")
        return "local"
    
    return "docker"

def setup_environment():
    """Set up the environment."""
    logger.info("Setting up environment...")
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Check if .env exists
    if not os.path.exists(".env"):
        logger.info("Creating .env file from example...")
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
        else:
            logger.error(".env.example not found")
            return False
    
    return True

def install_dependencies():
    """Install Python dependencies."""
    logger.info("Installing Python dependencies...")
    return run_command("pip install -r requirements.txt")

def initialize_database():
    """Initialize the database."""
    logger.info("Initializing database...")
    
    # Run database initialization
    if os.path.exists("scripts/init_db.py"):
        return run_command("python scripts/init_db.py")
    else:
        logger.warning("Database initialization script not found")
        return True

def deploy_docker():
    """Deploy using Docker Compose."""
    logger.info("Deploying with Docker Compose...")
    
    # Build and start services
    if not run_command("docker-compose build"):
        return False
    
    if not run_command("docker-compose up -d"):
        return False
    
    # Wait for services to be ready
    logger.info("Waiting for services to start...")
    import time
    time.sleep(10)
    
    # Initialize database in container
    run_command("docker-compose exec -T app python scripts/init_db.py")
    
    logger.info("Docker deployment complete!")
    logger.info("Application available at: http://localhost:8000")
    logger.info("API Documentation: http://localhost:8000/api/docs")
    logger.info("PGAdmin: http://localhost:5050")
    
    return True

def deploy_local():
    """Deploy locally."""
    logger.info("Deploying locally...")
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Initialize database
    if not initialize_database():
        return False
    
    # Start the application
    logger.info("Starting application...")
    logger.info("Application will be available at: http://localhost:8000")
    logger.info("API Documentation: http://localhost:8000/api/docs")
    
    # Run the application
    os.system("python -m uvicorn casebuilder.api.app:app --host 0.0.0.0 --port 8000 --reload")
    
    return True

def main():
    """Main deployment function."""
    logger.info("🚀 FILEBOSS Deployment Starting...")
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check dependencies
    deployment_type = check_dependencies()
    if not deployment_type:
        logger.error("Dependency check failed")
        return False
    
    # Setup environment
    if not setup_environment():
        logger.error("Environment setup failed")
        return False
    
    # Deploy based on available tools
    if deployment_type == "docker":
        success = deploy_docker()
    else:
        success = deploy_local()
    
    if success:
        logger.info("✅ FILEBOSS Deployment Complete!")
        logger.info("📊 Project indexed and ready for use")
    else:
        logger.error("❌ Deployment failed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)