"""
Verification and Build Script for LawGlance

This script:
1. Verifies Python is installed correctly
2. Installs all required dependencies
3. Creates a logo if one doesn't exist
4. Builds a standalone executable using PyInstaller
5. Provides clear instructions on next steps
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 60)
    print(message.center(60))
    print("=" * 60 + "\n")

def verify_python():
    """Verify Python is installed correctly with the right version."""
    print_header("VERIFYING PYTHON INSTALLATION")
    
    # Check Python version
    python_version = platform.python_version()
    py_version_tuple = tuple(map(int, python_version.split('.')))
    
    print(f"Found Python version: {python_version}")
    
    if py_version_tuple < (3, 8):
        print(f"ERROR: Python 3.8 or higher is required. You have {python_version}")
        return False
    
    print("Python version is adequate for LawGlance.")
    
    # Test for pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True, text=True)
        print("pip is installed and working correctly.")
    except subprocess.CalledProcessError:
        print("ERROR: pip is not installed or not working correctly.")
        return False
    
    return True

def install_dependencies():
    """Install all required dependencies."""
    print_header("INSTALLING DEPENDENCIES")
    
    # Core dependencies required for building
    core_deps = ["pyinstaller", "pillow", "setuptools", "wheel"]
    
    # Install core dependencies first
    print("Installing core build dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade"] + core_deps,
                      check=True)
        print("✓ Core dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install core dependencies: {str(e)}")
        return False
    
    # Install project requirements
    requirements_path = PROJECT_ROOT / "requirements.txt"
    if requirements_path.exists():
        print(f"Installing project requirements from {requirements_path}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
                          check=True)
            print("✓ Project requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Some requirements may have failed to install: {str(e)}")
    else:
        print(f"WARNING: requirements.txt not found at {requirements_path}")
        
    return True

def create_logo():
    """Create a logo if one doesn't exist."""
    print_header("CREATING LOGO")
    
    logo_dir = PROJECT_ROOT / "logo"
    logo_path = logo_dir / "logo.png"
    icon_path = logo_dir / "logo.ico"
    
    # Skip if icon already exists
    if icon_path.exists():
        print(f"Logo already exists at {icon_path}")
        return icon_path
    
    print(f"Logo icon not found at {icon_path}")
    print("Creating a new logo...")
    
    # Create logo directory if it doesn't exist
    logo_dir.mkdir(exist_ok=True)
    
    try:
        # Create a simple blue logo with white scales of justice
        from PIL import Image, ImageDraw
        
        # Create a blue background
        img = Image.new('RGB', (256, 256), color=(33, 150, 243))
        draw = ImageDraw.Draw(img)
        
        # Draw scales of justice in white
        # Horizontal bar
        draw.rectangle([64, 170, 192, 192], fill=(255, 255, 255))
        # Vertical stand
        draw.rectangle([118, 64, 138, 170], fill=(255, 255, 255))
        # Left scale
        draw.ellipse([64, 64, 114, 114], outline=(255, 255, 255), width=10)
        # Right scale
        draw.ellipse([162, 64, 212, 114], outline=(255, 255, 255), width=10)
        
        # Save as PNG
        img.save(logo_path, format="PNG")
        print(f"Created logo image at {logo_path}")
        
        # Save as ICO
        img.save(icon_path, format="ICO", sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print(f"Created logo icon at {icon_path}")
        
        return icon_path
    
    except ImportError:
        print("WARNING: PIL/Pillow not installed correctly. Cannot create logo.")
        print("You may need to run: pip install pillow")
        return None
    except Exception as e:
        print(f"ERROR: Failed to create logo: {str(e)}")
        return None

def build_executable():
    """Build a standalone executable using PyInstaller."""
    print_header("BUILDING EXECUTABLE")
    
    # Find icon path
    icon_path = PROJECT_ROOT / "logo" / "logo.ico"
    if not icon_path.exists():
        icon_path = create_logo()
    
    # Ensure the app.py file exists
    app_path = PROJECT_ROOT / "app.py"
    if not app_path.exists():
        print(f"ERROR: Main application file not found at {app_path}")
        return False
    
    print("Starting PyInstaller build process...")
    print("This may take several minutes. Please be patient.")
    
    # Command to build the executable
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LawGlance",
        "--onefile",
        "--windowed"
    ]
    
    # Add icon if available
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    # Add data files
    cmd.extend([
        "--add-data", f"logo{os.pathsep}logo",
    ])
    
    # Add common hidden imports for Streamlit applications
    cmd.extend([
        "--hidden-import=streamlit.web.bootstrap",
        "--hidden-import=streamlit.runtime.scriptrunner",
        "--hidden-import=langchain",
        "--hidden-import=langchain_openai",
    ])
    
    # Add main script
    cmd.append(str(app_path))
    
    # Run PyInstaller
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Executable built successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Build failed: {str(e)}")
        # Print any error output
        print("PyInstaller output:")
        print(e.stdout)
        print(e.stderr)
        return False

def provide_next_steps():
    """Provide clear instructions on next steps."""
    print_header("NEXT STEPS")
    
    # Determine where the executable should be
    exe_path = PROJECT_ROOT / "dist" / "LawGlance.exe"
    
    if exe_path.exists():
        print(f"Your LawGlance executable is ready at: {exe_path}")
        print("\nTo use LawGlance:")
        print("1. Create a file named '.env' in the same folder as the executable")
        print("2. Add your OpenAI API key to the .env file:")
        print("   OPENAI_API_KEY=your_api_key_here")
        print("3. Double-click LawGlance.exe to run the application")
        print("\nImportant Notes:")
        print("- The first run may take a few moments to start up")
        print("- Some antivirus software may flag PyInstaller-generated executables")
        print("  If this happens, you may need to add an exception")
    else:
        print("Could not find the LawGlance executable.")
        print("The build process may have failed or created the executable in a different location.")
        print("\nPlease check:")
        print("1. Look in the 'dist' directory for LawGlance.exe")
        print("2. Check the build output for any errors")
        print("3. Try running the build process again")

def main():
    """Main function to verify and build LawGlance."""
    print_header("LAWGLANCE VERIFICATION AND BUILD TOOL")
    
    print("This script will verify your environment and build LawGlance.")
    print("Press Ctrl+C at any time to cancel.\n")
    
    # Verify Python installation
    if not verify_python():
        print("Python verification failed. Please address the issues and try again.")
        return
    
    # Install dependencies
    if not install_dependencies():
        print("Dependency installation failed. Please address the issues and try again.")
        return
    
    # Create logo
    create_logo()
    
    # Build executable
    if not build_executable():
        print("Build failed. Please address the issues and try again.")
        return
    
    # Provide next steps
    provide_next_steps()
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
