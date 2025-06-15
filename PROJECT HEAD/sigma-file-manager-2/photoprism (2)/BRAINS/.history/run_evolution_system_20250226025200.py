#!/usr/bin/env python
"""
Run the Evolution System for Sorting Hat

This script starts the FastAPI server and opens the evolution dashboard.
"""
import os
import subprocess
import webbrowser
import time
import sys
from pathlib import Path

# Check if required modules are installed
try:
    import fastapi
    import uvicorn
    import nest_asyncio
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "nest_asyncio"])
    print("Packages installed successfully!")

def check_database():
    """Check if the evolution database exists, create if not"""
    db_path = Path(__file__).parent / "data" / "evolution.db"
    if not db_path.exists() or not db_path.parent.exists():
        print("Evolution database not found. Running initialization...")
        init_script = Path(__file__).parent / "initialize_evolution.py"
        subprocess.check_call([sys.executable, str(init_script)])
    else:
        print("Evolution database found.")

def start_server():
    """Start the FastAPI server"""
    print("Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--reload", "--port", "8000"],
        cwd=Path(__file__).parent
    )
    return server_process

def open_dashboard():
    """Open the evolution dashboard in the default browser"""
    dashboard_path = Path(__file__).parent / "evolution_dashboard.html"
    dashboard_url = f"file://{dashboard_path.absolute()}"
    print(f"Opening dashboard: {dashboard_url}")
    webbrowser.open(dashboard_url)

if __name__ == "__main__":
    print("Starting Evolution System...")
    
    # Ensure database exists
    check_database()
    
    # Start server
    server_process = start_server()
    
    try:
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(2)
        
        # Open dashboard
        open_dashboard()
        
        print("\nEvolution System is running!")
        print("Press Ctrl+C to stop the server and exit.")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()
        print("Server stopped. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        server_process.terminate()
