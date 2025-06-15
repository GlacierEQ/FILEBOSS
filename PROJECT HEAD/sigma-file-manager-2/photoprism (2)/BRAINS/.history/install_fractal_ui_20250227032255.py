#!/usr/bin/env python
"""
Install Fractal UI Components

This script provides a complete installation of the fractal UI enhancement.
It handles dependency installation, image generation, and configuration.
"""
import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
import argparse

def print_header(text):
    """Print a styled header"""
    print("\n" + "=" * 70)
    print(f"{text.center(70)}")
    print("=" * 70 + "\n")

def print_step(text):
    """Print a step in the process"""
    print(f"➤ {text}")

def print_success(text):
    """Print a success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"❌ {text}")

def install_dependencies():
    """Install required dependencies"""
    print_step("Installing required dependencies...")
    
    packages = [
        "numpy",
        "pillow",
        "requests",
        "colorama"
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print_success("Installed dependencies successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error installing dependencies: {e}")
        return False

def generate_fractal_images():
    """Generate fractal images using the generator script"""
    print_step("Generating fractal images...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fractal_generator = os.path.join(base_dir, "fractal_generator.py")
    
    if not os.path.exists(fractal_generator):
        print_error(f"Fractal generator script not found: {fractal_generator}")
        return False
        
    try:
        subprocess.check_call([sys.executable, fractal_generator, "--all"])
        print_success("Generated fractal images successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error generating fractal images: {e}")
        return False

def setup_theme():
    """Set up the fractal theme"""
    print_step("Setting up fractal theme...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    theme_setup = os.path.join(base_dir, "apply_fractal_theme.py")
    
    if not os.path.exists(theme_setup):
        print_error(f"Theme setup script not found: {theme_setup}")
        return False
        
    try:
        subprocess.check_call([sys.executable, theme_setup])
        print_success("Applied fractal theme successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error setting up theme: {e}")
        return False

def create_desktop_shortcut():
    """Create a desktop shortcut to the fractal dashboard"""
    print_step("Creating desktop shortcut...")
    
    # Get desktop path
    if platform.system() == "Windows":
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    elif platform.system() == "Darwin":  # macOS
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    else:  # Linux
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_file = os.path.join(base_dir, "dashboard.html")
    
    if not os.path.exists(dashboard_file):
        print_error(f"Dashboard file not found: {dashboard_file}")
        return False
        
    try:
        if platform.system() == "Windows":
            # Create a .lnk file for Windows
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(os.path.join(desktop_path, "Sorting Hat Dashboard.lnk"))
            shortcut.Targetpath = dashboard_file
            shortcut.WorkingDirectory = base_dir
            shortcut.Description = "Sorting Hat Dashboard with Fractal UI"
            shortcut.IconLocation = os.path.join(base_dir, "static", "images", "logo-fractal.png")
            shortcut.save()
        else:
            # Create a .desktop file for Linux/macOS
            shortcut_path = os.path.join(desktop_path, "sorting-hat-dashboard.desktop")
            with open(shortcut_path, "w") as f:
                f.write("[Desktop Entry]\n")
                f.write("Type=Application\n")
                f.write("Name=Sorting Hat Dashboard\n")
                f.write(f"Exec=xdg-open {dashboard_file}\n")
                f.write("Icon=system-file-manager\n")
                f.write("Comment=Sorting Hat Dashboard with Fractal UI\n")
                f.write("Terminal=false\n")
                
            # Make it executable
            os.chmod(shortcut_path, 0o755)
            
        print_success("Created desktop shortcut successfully")
        return True
    except Exception as e:
        print_error(f"Error creating desktop shortcut: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Install Fractal UI components")
    parser.add_argument("--no-dependencies", action="store_true", help="Skip dependency installation")
    parser.add_argument("--no-images", action="store_true", help="Skip image generation")
    parser.add_argument("--desktop-shortcut", action="store_true", help="Create desktop shortcut")
    
    args = parser.parse_args()
    
    print_header("SORTING HAT FRACTAL UI INSTALLATION")
    
    success = True
    
    if not args.no_dependencies:
        success = success and install_dependencies()
        
    if not args.no_images:
        success = success and generate_fractal_images()
        
    success = success and setup_theme()
    
    if args.desktop_shortcut:
        success = success and create_desktop_shortcut()
    
    if success:
        print_header("INSTALLATION SUCCESSFUL")
        print("The Fractal UI has been successfully installed!")
        print("\nTo view the new interface, open:")
        print("  - dashboard.html in your web browser")
        print("  - or restart the web server if running")
    else:
        print_header("INSTALLATION INCOMPLETE")
        print("Some components could not be installed. Please check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
