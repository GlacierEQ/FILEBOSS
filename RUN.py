#!/usr/bin/env python3
# -------------------------------------------------------------------
#  CaseBuilder - The Ultimate Installer & Runner
#  Just run this file: python run.py
# -------------------------------------------------------------------

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

VENV_DIR = ".venv"

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
    """Creates and activates a virtual environment."""
    print("\nStep 2: Setting up virtual environment...")
    venv_path = Path(VENV_DIR)
    if venv_path.exists():
        print("✅ Virtual environment already exists.")
        return

    print(f"   Creating virtual environment in ./{VENV_DIR}/")
    try:
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True, capture_output=True)
        print("✅ Virtual environment created.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to create virtual environment.")
        print(e.stderr.decode())
        sys.exit(1)

def get_pip_path():
    """Gets the path to the pip executable in the venv."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    return os.path.join(VENV_DIR, "bin", "pip")

def get_python_path():
    """Gets the path to the python executable in the venv."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")

def install_dependencies():
    """Installs dependencies from requirements.txt into the venv."""
    print("\nStep 3: Installing dependencies...")
    pip_path = get_pip_path()
    requirements_path = "requirements.txt"
    try:
        subprocess.run([pip_path, "install", "-r", requirements_path], check=True, capture_output=True)
        print("✅ All dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install dependencies.")
        print(e.stderr.decode())
        sys.exit(1)

def launch_application():
    """Launches the FastAPI application using the venv's python."""
    print("\nStep 4: Launching CaseBuilder Application...")
    python_path = get_python_path()
    
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
        subprocess.run([python_path, "main.py"])
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
    main()
