#!/usr/bin/env python
"""
Dependency Installer for Sorting Hat

This script installs all required Python packages for the Sorting Hat system.
"""
import subprocess
import sys
import os
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
try:
    init()
except:
    # If colorama isn't installed yet
    pass

def print_header(text):
    """Print a colored header."""
    try:
        print(f"\n{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text.center(50)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}\n")
    except:
        # Fallback if colorama isn't installed yet
        print("\n" + "=" * 50)
        print(text.center(50))
        print("=" * 50 + "\n")

def print_success(text):
    """Print a success message."""
    try:
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
    except:
        print(f"✓ {text}")

def print_error(text):
    """Print an error message."""
    try:
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")
    except:
        print(f"✗ {text}")

def install_package(package):
    """Install a Python package using pip."""
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print_success(f"Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install {package}: {e}")
        return False

def check_package(package):
    """Check if a package is installed."""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    print_header("SORTING HAT DEPENDENCY INSTALLER")
    
    # Core dependencies
    core_packages = [
        "fastapi", 
        "uvicorn", 
        "watchdog", 
        "psutil", 
        "requests", 
        "colorama",
        "nest-asyncio",
        "python-dotenv",
        "pydantic",
        "tabulate"
    ]
    
    # Optional dependencies
    optional_packages = [
        "groq",
        "agentops",
        "pywin32"  # Windows-specific
    ]
    
    # Install core dependencies
    print("Installing core dependencies...")
    all_core_installed = True
    for package in core_packages:
        if not check_package(package.split("==")[0].replace("-", "_")):
            success = install_package(package)
            if not success:
                all_core_installed = False
        else:
            print_success(f"{package} is already installed")
    
    # Install optional dependencies
    print("\nInstalling optional dependencies...")
    for package in optional_packages:
        try:
            if package == "pywin32" and os.name != 'nt':
                print(f"Skipping {package} (not on Windows)")
                continue
                
            if not check_package(package.split("==")[0].replace("-", "_")):
                install_package(package)
            else:
                print_success(f"{package} is already installed")
        except:
            print(f"Optional package {package} could not be installed")
    
    if all_core_installed:
        print_header("INSTALLATION COMPLETE")
        print("All core dependencies have been installed successfully!")
        print("\nNext steps:")
        print("1. Run 'python initialize_evolution.py' to set up the database")
        print("2. Start the server with 'python run_sorting_service.py'")
        print("3. Open spaceship_dashboard.html or dashboard.html in your browser\n")
    else:
        print_header("INSTALLATION INCOMPLETE")
        print("Some dependencies could not be installed.")
        print("Please check the error messages above and try again.\n")

if __name__ == "__main__":
    main()
