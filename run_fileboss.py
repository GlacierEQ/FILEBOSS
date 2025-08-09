""
FileBoss Launcher

This script launches the FileBoss application with a modern GUI interface.
"""

import sys
import os
import logging
from pathlib import Path

def setup_logging():
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'fileboss.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check and install required dependencies."""
    try:
        import PyQt6
        import sqlalchemy
        import watchdog
        return True
    except ImportError:
        print("Installing required dependencies...")
        try:
            import subprocess
            import sys
            subprocess.check_call([
                sys.executable, 
                "-m", 
                "pip", 
                "install", 
                "-r", 
                "requirements.txt"
            ])
            return True
        except Exception as e:
            print(f"Failed to install dependencies: {e}")
            return False

def main():
    """Main entry point for the application."""
    # Set up logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        print("Failed to install required dependencies. Please check the logs.")
        return 1
    
    # Import GUI after dependencies are checked
    from casebuilder.gui.main_window import run_gui
    
    try:
        # Run the GUI application
        print("Starting FileBoss...")
        run_gui()
        return 0
    except Exception as e:
        logging.error("Fatal error in FileBoss", exc_info=True)
        print(f"A fatal error occurred: {e}")
        print("Please check the log file for more details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
