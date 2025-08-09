#!/usr/bin/env python3
"""
SIGMA FILEBOSS Launcher
Main entry point for the unified file management system
"""

import sys
import os
import logging
import argparse
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "sigma_fileboss.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set specific loggers
    logging.getLogger("PyQt6").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

def check_dependencies():
    """Check if required dependencies are available."""
    required_packages = [
        "PyQt6",
        "sqlalchemy",
        "requests",
        "PIL"
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print("Please install them using: pip install -r requirements_sigma.txt")
        return False

    return True

def setup_environment():
    """Setup environment variables and configuration."""
    # Set Qt platform plugin path
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "")

    # Set application data directory
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    os.environ.setdefault("FILEBOSS_DATA_DIR", str(data_dir))

    # Set default database URL
    db_path = data_dir / "sigma_fileboss.db"
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")

    # Create necessary directories
    for dir_name in ["logs", "temp", "exports", "organized"]:
        (PROJECT_ROOT / dir_name).mkdir(exist_ok=True)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="SIGMA FILEBOSS - Unified File Management System")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    parser.add_argument("--demo-mode", action="store_true",
                       help="Run in demo mode with limited functionality")
    parser.add_argument("--tab", type=str,
                       help="Start with specific tab active")

    args = parser.parse_args()

    # Setup
    setup_logging(args.log_level)
    setup_environment()

    logger = logging.getLogger(__name__)
    logger.info("Starting SIGMA FILEBOSS...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    try:
        # Import and run the main application
        from sigma_fileboss_main import main as app_main

        # Set demo mode if requested
        if args.demo_mode:
            os.environ["DEMO_MODE"] = "1"
            logger.info("Running in demo mode")

        # Set initial tab if specified
        if args.tab:
            os.environ["INITIAL_TAB"] = args.tab
            logger.info(f"Starting with {args.tab} tab active")

        # Launch the application
        logger.info("Launching GUI application...")
        app_main()

    except ImportError as e:
        logger.error(f"Failed to import main application: {e}")
        print("\nError: Could not start SIGMA FILEBOSS.")
        print("Please ensure all components are properly installed.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
