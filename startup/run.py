#!/usr/bin/env python3
# -------------------------------------------------------------------
#  CaseBuilder - The Ultimate Installer & Runner
#  Just run this file: python startup/run.py
# -------------------------------------------------------------------

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

# Adjust paths to be relative to the project root (one level up)
PROJECT_ROOT = Path(__file__).parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"

def check_python_version():
    """Checks if the Python version is 3.8+."""
    print("Step 1: Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"❌ ERROR: Python 3.8+ is required. You have {sys.version_info.major}.{sys.version_info.minor}.")
        print("   Please upgrade your Python version and try again.")
        sys.exit(1)
    print(f"✅ Python version is compatible ({sys.version_info.major}.{sys.version_info.minor}).")
    return True

def setup_virtual_environment():
    """Creates and activates a virtual environment in the project root."""
    print("\nStep 2: Setting up virtual environment...")
    if VENV_DIR.exists():
        print("✅ Virtual environment already exists.")
        return

    print(f"   Creating virtual environment in ./{VENV_DIR.name}/")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True, capture_output=True)
        print("✅ Virtual environment created.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to create virtual environment.")
        print(e.stderr.decode())
        sys.exit(1)

def get_pip_path():
    """Gets the path to the pip executable in the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def get_python_path():
    """Gets the path to the python executable in the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def install_dependencies():
    """Installs dependencies from requirements.txt into the venv."""
    print("\nStep 3: Installing dependencies...")
    pip_path = get_pip_path()
    requirements_path = PROJECT_ROOT / "requirements.txt"
    try:
        subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True, capture_output=True, cwd=PROJECT_ROOT)
        print("�� All dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install dependencies.")
        print(e.stderr.decode())
        sys.exit(1)

def launch_application():
    """Launches the FastAPI application using the venv's python."""
    print("\nStep 4: Launching CaseBuilder Application...")
    python_path = get_python_path()
    main_py_path = PROJECT_ROOT / "main.py"
    
    print("--------------------------------------------------------")
    print("🚀 Server is starting! Your app will be live at:")
    print("   http://127.0.0.1:8000")
    print("   API Docs will open automatically in your browser.")
    print("   Press CTRL+C to stop the server.")
    print("--------------------------------------------------------")

    # Use a thread to open the browser after a delay
    def open_browser():
        time.sleep(3) # Wait for server to start
        webbrowser.open("http://127.0.0.1:8000/docs")
    
    threading.Thread(target=open_browser).start()

    try:
        # Run from the project root directory
        subprocess.run([str(python_path), str(main_py_path)], cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ ERROR: Failed to launch application: {e}")
        sys.exit(1)

def main():
    """The main function to orchestrate the setup and run process."""
    print("========================================================")
    print("    🏛️  Welcome to the CaseBuilder Operator Console")
    print("========================================================")
    
    check_python_version()
    setup_virtual_environment()
    install_dependencies()
    launch_application()

if __name__ == "__main__":
    # Change to the project's root directory to ensure all paths are correct
    os.chdir(PROJECT_ROOT)
    main()
