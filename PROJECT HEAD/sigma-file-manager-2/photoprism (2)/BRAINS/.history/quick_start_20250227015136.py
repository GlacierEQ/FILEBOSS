#!/usr/bin/env python
"""
Quick Start Script for Sorting Hat

This script installs dependencies, initializes the system, and starts the server
with proper error handling at each step.
"""
import os
import sys
import subprocess
import time
import platform
from pathlib import Path

def print_step(step_num, text):
    """Print a step header."""
    print(f"\n[STEP {step_num}] {text}")
    print("-" * 50)

def run_command(command, shell=False):
    """Run a command and return success status."""
    print(f"Running: {' '.join(command) if isinstance(command, list) else command}")
    try:
        if shell:
            subprocess.check_call(command, shell=True)
        else:
            subprocess.check_call(command)
        print("✓ Command completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Command failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"✗ Command not found")
        return False

def check_file_exists(path):
    """Check if a file exists."""
    return os.path.exists(path)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    print("\n" + "=" * 50)
    print("SORTING HAT QUICK START".center(50))
    print("=" * 50)
    print(f"Working directory: {base_dir}")
    
    # Step 1: Install dependencies
    print_step(1, "Installing dependencies")
    
    # Try to install the installer's dependencies first if needed
    if not run_command([sys.executable, "-m", "pip", "install", "colorama"]):
        print("Continuing without colorama...")
    
    # Run the dependency installer if it exists
    installer_path = os.path.join(base_dir, "install_dependencies.py")
    if check_file_exists(installer_path):
        run_command([sys.executable, installer_path])
    else:
        print("Dependency installer not found, installing core packages directly...")
        core_packages = ["fastapi", "uvicorn", "watchdog", "psutil", "requests", "colorama", "python-dotenv"]
        for package in core_packages:
            run_command([sys.executable, "-m", "pip", "install", package])
    
    # Step 2: Kill any existing uvicorn processes
    print_step(2, "Cleaning up existing processes")
    if platform.system() == "Windows":
        run_command("taskkill /f /im uvicorn.exe 2>NUL", shell=True)
    else:
        run_command("pkill uvicorn 2>/dev/null || true", shell=True)
    
    # Step 3: Initialize the evolution system
    print_step(3, "Initializing evolution system")
    evolution_init = os.path.join(base_dir, "initialize_evolution.py")
    if check_file_exists(evolution_init):
        run_command([sys.executable, evolution_init])
    else:
        print("Evolution initializer not found, creating basic directory structure...")
        safe_path = os.path.join(os.path.expanduser("~"), "OrganizeFolder")
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(safe_path, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created directories: {safe_path}, {data_dir}")
    
    # Step 4: Start the service
    print_step(4, "Starting the Sorting Hat service")
    service_manager = os.path.join(base_dir, "service_manager.py")
    if check_file_exists(service_manager):
        # Start in a separate process that won't be killed when this script exits
        if platform.system() == "Windows":
            subprocess.Popen(f"start cmd /c \"{sys.executable} {service_manager}\"", shell=True)
        else:
            subprocess.Popen(f"{sys.executable} {service_manager} &", shell=True)
        print("Service started in a separate window")
    else:
        print("Service manager not found, starting server directly...")
        if check_file_exists(os.path.join(base_dir, "server.py")):
            # Start in a separate process
            if platform.system() == "Windows":
                subprocess.Popen(f"start cmd /c \"{sys.executable} -m uvicorn server:app --reload\"", shell=True)
            else:
                subprocess.Popen(f"{sys.executable} -m uvicorn server:app --reload &", shell=True)
            print("Server started in a separate window")
        else:
            print("Error: server.py not found!")
            return False
    
    # Step 5: Wait for server to start
    print_step(5, "Waiting for server to initialize")
    print("Giving the server time to start...")
    for i in range(5, 0, -1):
        print(f"Opening dashboard in {i} seconds...", end="\r")
        time.sleep(1)
    print("\nServer should be running now!")
    
    # Step 6: Open the dashboard
    print_step(6, "Opening dashboard")
    dashboard_file = os.path.join(base_dir, "spaceship_dashboard.html")
    regular_dashboard = os.path.join(base_dir, "dashboard.html")
    if check_file_exists(dashboard_file):
        if platform.system() == "Windows":
            os.startfile(dashboard_file)
        else:
            run_command(["xdg-open", dashboard_file])
        print("Opened spaceship dashboard")
    elif check_file_exists(regular_dashboard):
        if platform.system() == "Windows":
            os.startfile(regular_dashboard)
        else:
            run_command(["xdg-open", regular_dashboard])
        print("Opened regular dashboard")
    else:
        print("Dashboard file not found.")
    
    print("\n" + "=" * 50)
    print("SORTING HAT IS RUNNING".center(50))
    print("=" * 50)
    print("\nThe system should now be up and running!")
    print("\nIf you encounter issues:")
    print("1. Run 'python troubleshoot.py' to diagnose problems")
    print("2. Check the log file: sorting_service.log")
    print("3. Make sure port 8000 is available")
    print("\nTo stop the service, close the command window or press Ctrl+C in the service window.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            # Keep the script running to show the output
            input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
    except Exception as e:
        print(f"\nError during setup: {e}")
        input("Press Enter to exit...")
