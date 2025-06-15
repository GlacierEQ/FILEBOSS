#!/usr/bin/env python
"""
Sorting Hat System Troubleshooter

This script checks for common issues with the Sorting Hat system and provides
recommendations for fixing them.
"""
import os
import sys
import socket
import subprocess
import platform
import time
from pathlib import Path

def print_header(text):
    """Print header text."""
    print("\n" + "=" * 60)
    print(text.center(60))
    print("=" * 60)

def print_status(text, status, details=None):
    """Print a status line."""
    status_text = "[ OK ]" if status else "[FAIL]"
    status_color = "\033[92m" if status else "\033[91m"
    reset_color = "\033[0m"
    
    # Check if terminal supports colors
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        print(f"{status_color}{status_text}{reset_color} {text}")
    else:
        print(f"{status_text} {text}")
        
    if details and not status:
        print(f"      ↳ {details}")

def check_port(port):
    """Check if a port is in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def check_process_running(process_name):
    """Check if a process is running."""
    if platform.system() == "Windows":
        output = subprocess.check_output(["tasklist", "/FI", f"IMAGENAME eq {process_name}"], text=True)
        return process_name in output
    else:
        try:
            subprocess.check_output(["pgrep", "-f", process_name])
            return True
        except subprocess.CalledProcessError:
            return False

def check_file_exists(file_path):
    """Check if a file exists."""
    return os.path.exists(file_path)

def check_directory_writable(dir_path):
    """Check if a directory is writable."""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            return True
        except:
            return False
    return os.access(dir_path, os.W_OK)

def run_troubleshooter():
    print_header("SORTING HAT SYSTEM TROUBLESHOOTER")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Base directory: {base_dir}")
    
    # Check Python version
    python_version = platform.python_version()
    python_ok = int(python_version.split('.')[0]) >= 3 and int(python_version.split('.')[1]) >= 7
    print_status(f"Python version: {python_version}", python_ok, "Python 3.7 or higher required")
    
    # Check critical files
    server_file = os.path.join(base_dir, "server.py")
    server_exists = check_file_exists(server_file)
    print_status("Server file exists", server_exists)
    
    watch_file = os.path.join(base_dir, "watch_files.py")
    watch_exists = check_file_exists(watch_file)
    print_status("Watch file exists", watch_exists)
    
    evolution_dir = os.path.join(base_dir, "data")
    evolution_db = os.path.join(evolution_dir, "evolution.db")
    db_exists = check_file_exists(evolution_db)
    print_status("Evolution database exists", db_exists, 
                f"Run 'python initialize_evolution.py' to create it")
    
    # Check safe path
    safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
    safe_path_exists = os.path.exists(safe_path)
    print_status(f"Safe path exists: {safe_path}", safe_path_exists)
    
    if safe_path_exists:
        safe_path_writable = check_directory_writable(safe_path)
        print_status("Safe path is writable", safe_path_writable)
    
    # Check if server is running
    server_port_in_use = check_port(8000)
    print_status("Server running on port 8000", server_port_in_use)
    
    # Check processes
    uvicorn_running = check_process_running("uvicorn") or check_process_running("uvicorn.exe")
    print_status("Uvicorn process running", uvicorn_running)
    
    python_running = check_process_running("python") or check_process_running("python.exe")
    print_status("Python processes running", python_running)
    
    # Results and recommendations
    print_header("TROUBLESHOOTING RESULTS")
    
    if not server_exists or not watch_exists:
        print("\n⚠️  Critical files missing!")
        print("Make sure you have all the necessary files in the correct directory.")
    
    if not db_exists:
        print("\n⚠️  Evolution database is missing!")
        print("Run 'python initialize_evolution.py' to create it.")
    
    if not safe_path_exists:
        print("\n⚠️  Safe path doesn't exist!")
        print(f"Creating directory: {safe_path}")
        try:
            os.makedirs(safe_path, exist_ok=True)
            print("✓ Directory created successfully.")
        except Exception as e:
            print(f"✗ Failed to create directory: {e}")
    
    if not server_port_in_use:
        print("\n⚠️  Server is not running!")
        print("Run 'python service_manager.py' to start the server.")
        print("Or run 'python run_sorting_service.py' to start the service with a monitor.")
    
    if all([server_exists, watch_exists, db_exists, safe_path_exists, server_port_in_use]):
        print("\n✅ All checks passed! System appears to be running correctly.")
        print("If you're still having issues:")
        print("1. Check the log file at: sorting_service.log")
        print("2. Make sure your API keys are configured correctly")
        print("3. Try restarting the system with: python run_sorting_service.py")
    
    print("\nTry running one of the following commands to start the system:")
    print("1. python run_sorting_service.py  (recommended)")
    print("2. python service_manager.py")
    print("3. uvicorn server:app --reload (for development)")

if __name__ == "__main__":
    run_troubleshooter()
