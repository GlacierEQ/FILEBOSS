"""
Quick script to create a standalone executable for LawGlance.
This is a simplified alternative to the full build_desktop_app.py
that focuses just on creating a basic executable.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

def ensure_logo_exists():
    """Make sure we have a logo/icon for the application."""
    logo_path = PROJECT_ROOT / "logo" / "logo.png"
    icon_path = PROJECT_ROOT / "logo" / "logo.ico"
    
    if not icon_path.exists():
        print("Creating logo and icon files...")
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "create_placeholder_logo", 
                PROJECT_ROOT / "logo" / "create_placeholder_logo.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.create_placeholder_logo()
        except Exception as e:
            print(f"Warning: Could not create logo: {e}")
            print("Continuing without icon...")

def build_exe():
    """Build the executable using PyInstaller."""
    print("\nBuilding LawGlance executable...")
    
    # Make sure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Ensure we have an icon
    ensure_logo_exists()
    
    # Determine icon path
    icon_path = PROJECT_ROOT / "logo" / "logo.ico"
    icon_arg = f"--icon={icon_path}" if icon_path.exists() else ""
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LawGlance",
        "--onefile",
        "--windowed",
        icon_arg,
        "--add-data", f"logo{os.pathsep}logo",
        "--add-data", f".env{os.pathsep}.",
        "--hidden-import=streamlit.web.bootstrap",
        "--hidden-import=langchain",
        "--hidden-import=langchain_openai",
        "--hidden-import=langchain_chroma",
        "app.py"
    ]
    
    # Filter out empty arguments
    cmd = [arg for arg in cmd if arg]
    
    # Run PyInstaller
    try:
        subprocess.check_call(cmd)
        print("\n✅ Build successful!")
        print(f"Executable created at: {PROJECT_ROOT / 'dist' / 'LawGlance.exe'}")
        print("\nYou can now distribute this executable to run LawGlance without Python installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("LawGlance Quick Executable Builder")
    print("=" * 60)
    
    # Ask if the user wants to continue
    response = input("This will create a standalone EXE file. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Build cancelled.")
        sys.exit(0)
    
    # Check if we're on Windows
    if platform.system() != "Windows":
        print("Warning: Building Windows executable on non-Windows system.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Build cancelled.")
            sys.exit(0)
    
    # Build the executable
    build_exe()
