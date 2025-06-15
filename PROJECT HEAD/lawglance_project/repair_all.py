"""
Complete LawGlance Project Repair Script

This script fixes all common issues in the LawGlance project:
1. Fixes build_desktop_app.py syntax and duplications
2. Resolves dependency conflicts
3. Creates necessary files and directories
4. Ensures icon paths are correct
5. Sets up a proper environment for building
"""
import os
import sys
import subprocess
import shutil
import json
import re
from pathlib import Path
import importlib.util
from datetime import datetime

# Define project root
PROJECT_ROOT = Path(__file__).parent

# Define color codes for console output
if sys.platform == "win32":
    # Windows color codes
    GREEN = ''
    RED = ''
    BLUE = ''
    YELLOW = ''
    NC = ''  # No Color
else:
    # Unix color codes
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color

def print_header(message):
    """Print a nicely formatted header."""
    print("\n" + "=" * 70)
    print(f"{BLUE} {message}{NC}")
    print("=" * 70)

def print_success(message):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{NC}")

def print_error(message):
    """Print an error message."""
    print(f"{RED}✗ {message}{NC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{YELLOW}! {message}{NC}")

def run_command(command, verbose=True):
    """Run a shell command and return the result."""
    if verbose:
        print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command, 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if verbose and result.stdout:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if verbose and e.stderr:
            print(f"Error: {e.stderr}")
        return False, e.stderr

def check_python_environment():
    """Check that we have a compatible Python environment."""
    print_header("Checking Python Environment")
    
    # Check Python version
    py_version = sys.version_info
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
        print_error(f"Python 3.8+ required, found {sys.version}")
        return False
    
    print_success(f"Python version {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (compatible)")
    
    # Check for pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL)
        print_success("pip is installed and working")
    except:
        print_error("pip is not installed or not working")
        return False
    
    return True

def fix_project_structure():
    """Fix the project directory structure."""
    print_header("Fixing Project Structure")
    
    # Create necessary directories if they don't exist
    dirs_to_create = ['src', 'logo', 'data', 'build', 'dist', 'output', 'scripts']
    for dir_name in dirs_to_create:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print_success(f"Created directory: {dir_name}")
        else:
            print(f"Directory already exists: {dir_name}")
    
    return True

def fix_logo():
    """Fix the logo and icon files."""
    print_header("Fixing Logo Files")
    
    logo_dir = PROJECT_ROOT / "logo"
    icon_path = logo_dir / "logo.ico"
    png_path = logo_dir / "logo.png"
    
    # If icon already exists, we're done
    if icon_path.exists() and png_path.exists():
        print_success(f"Logo files already exist")
        return icon_path
    
    print("Creating logo files...")
    try:
        # First try to install pillow if needed
        try:
            import PIL
        except ImportError:
            print("Installing Pillow...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        
        # Now create the logo
        from PIL import Image, ImageDraw
        
        # Create a blue background with scales of justice
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
        img.save(png_path)
        print_success(f"Created PNG logo at {png_path}")
        
        # Save as ICO
        img.save(icon_path, sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print_success(f"Created ICO logo at {icon_path}")
        
        return icon_path
    except Exception as e:
        print_error(f"Failed to create logo: {str(e)}")
        return None

def fix_build_desktop_app():
    """Fix the build_desktop_app.py file."""
    print_header("Fixing build_desktop_app.py")
    
    build_file = PROJECT_ROOT / "build_desktop_app.py"
    
    # If file doesn't exist, create it
    if not build_file.exists():
        print("Creating build_desktop_app.py...")
        fixed_content = create_build_desktop_app_content()
        with open(build_file, 'w') as f:
            f.write(fixed_content)
        print_success(f"Created build_desktop_app.py")
        return True
    
    # If file exists, back it up and replace with fixed version
    print(f"Backing up existing build_desktop_app.py...")
    backup_file = build_file.with_suffix(".py.bak")
    shutil.copy2(build_file, backup_file)
    
    # Create fixed content
    fixed_content = create_build_desktop_app_content()
    
    # Write fixed content
    with open(build_file, 'w') as f:
        f.write(fixed_content)
    
    print_success(f"Fixed build_desktop_app.py (backup saved as {backup_file.name})")
    return True

def create_build_desktop_app_content():
    """Create the content for a fixed build_desktop_app.py file."""
    icon_path = PROJECT_ROOT / "logo" / "logo.ico"
    
    content = f"""# filepath: {PROJECT_ROOT / 'build_desktop_app.py'}
\"\"\"
Build script for creating the LawGlance desktop application.
This fixed version uses absolute paths to avoid path resolution issues.
\"\"\"
import os
import sys
import subprocess
import shutil
from pathlib import Path
import PyInstaller.__main__

# Define project directory (absolute path)
PROJECT_ROOT = Path(__file__).parent.resolve()

def create_logo():
    \"\"\"Create a logo if one doesn't exist, and return the path to the icon file.\"\"\"
    logo_dir = PROJECT_ROOT / "logo"
    logo_dir.mkdir(exist_ok=True)
    
    icon_path = logo_dir / "logo.ico"
    png_path = logo_dir / "logo.png"
    
    # If icon already exists, return its path
    if icon_path.exists():
        print(f"Using existing icon at {{icon_path}}")
        return str(icon_path)
    
    print("Creating logo since none exists...")
    try:
        # Try to create a simple logo using PIL
        from PIL import Image, ImageDraw
        
        # Create a blue background with scales of justice
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
        img.save(png_path)
        print(f"Created logo image at {{png_path}}")
        
        # Save as ICO for Windows
        img.save(icon_path, sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print(f"Created icon at {{icon_path}}")
        
        return str(icon_path)
    
    except ImportError:
        print("Warning: PIL/Pillow not installed. Cannot create logo.")
        print("Installing Pillow...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            print("Pillow installed. Retrying logo creation...")
            return create_logo()  # Try again
        except Exception as e:
            print(f"Error installing Pillow: {{str(e)}}")
            return None
    
    except Exception as e:
        print(f"Error creating logo: {{str(e)}}")
        return None

def build_executable():
    \"\"\"Build the executable using PyInstaller.\"\"\"
    print("Building executable...")
    
    # Get icon path and create if needed
    icon_path = create_logo()
    
    # Build command for PyInstaller
    cmd = [
        '--name=LawGlance',
        '--onefile',
        '--windowed',
        '--clean',
        '--distpath=dist/LawGlance',
        '--workpath=build',
        '--specpath=build',
    ]
    
    # Add icon if one was created
    if icon_path:
        cmd.append(f'--icon={{icon_path}}')
    
    # Add required hidden imports for streamlit
    cmd.extend([
        '--hidden-import=streamlit.web.bootstrap',
        '--hidden-import=streamlit.runtime.scriptrunner',
        '--hidden-import=langchain',
        '--hidden-import=langchain_openai',
    ])
    
    # Add data folders
    cmd.extend([
        '--add-data', f'logo{{os.pathsep}}logo',
    ])
    
    # Add the main script to build
    cmd.append('app.py')
    
    # Run PyInstaller
    try:
        PyInstaller.__main__.run(cmd)
        print("Executable built successfully.")
        return True
    except Exception as e:
        print(f"Error building executable: {{str(e)}}")
        return False

def create_installer():
    \"\"\"Create an installer using Inno Setup.\"\"\"
    print("Creating installer...")
    
    # Check if Inno Setup is installed
    inno_setup_path = r"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if not os.path.exists(inno_setup_path):
        print("Inno Setup not found. Please install it to create an installer.")
        return False
    
    # Create a basic installer script if one doesn't exist
    iss_file = PROJECT_ROOT / "installer.iss"
    if not iss_file.exists():
        with open(iss_file, 'w') as f:
            f.write(r\"\"\"
; Inno Setup Script for LawGlance
#define MyAppName "LawGlance"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LawGlance Team"
#define MyAppURL "https://www.lawglance.com/"
#define MyAppExeName "LawGlance.exe"

[Setup]
AppId={{9B30D1A7-8F7D-4A5E-9E7C-A2F4D73A65E8}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
OutputBaseFilename=LawGlance-Setup
SetupIconFile=logo\\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "dist\\LawGlance\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
\"\"\")
    
    # Run Inno Setup
    try:
        subprocess.check_call([inno_setup_path, str(iss_file)])
        print("Installer created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating installer: {{str(e)}}")
        return False
    except FileNotFoundError:
        print(f"Inno Setup executable not found at {{inno_setup_path}}")
        return False

def create_portable():
    \"\"\"Create a portable ZIP version.\"\"\"
    print("Generating portable version...")
    
    # Make sure the output directory exists
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Check if the executable exists
    exe_dir = PROJECT_ROOT / "dist" / "LawGlance"
    if not exe_dir.exists():
        print("Executable directory not found. Build the executable first.")
        return False
    
    # Create the ZIP file
    try:
        import shutil
        zip_path = output_dir / "LawGlance-Portable"
        shutil.make_archive(str(zip_path), 'zip', exe_dir)
        print(f"Portable version created at {{zip_path}}.zip")
        return True
    except Exception as e:
        print(f"Error creating portable version: {{str(e)}}")
        return False

def main():
    print("Welcome to the LawGlance Desktop Application Builder!")
    print("Please select build options:")
    print("1. Build Executable")
    print("2. Create Installer")
    print("3. Generate Portable Version")
    
    choice = input("Enter your choice (1/2/3): ")
    
    if choice == '1':
        build_executable()
    elif choice == '2':
        if not build_executable():
            print("Failed to build executable, cannot create installer.")
            return
        create_installer()
    elif choice == '3':
        if not build_executable():
            print("Failed to build executable, cannot create portable version.")
            return
        create_portable()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
"""
    return content

def fix_dependencies():
    """Fix dependency conflicts."""
    print_header("Fixing Dependencies")
    
    # Define compatible versions
    compatible_versions = {
        "langchain-core": "0.1.33",
        "langchain": "0.1.13",
        "langchain-text-splitters": "0.1.0",
        "tokenizers": "0.15.0",
        "transformers": "4.36.2",
        "tiktoken": "0.7.0",
        "python-dotenv": "1.0.0",
    }
    
    # Packages to uninstall first
    packages_to_uninstall = [
        "langchain",
        "langchain-core",
        "langchain-text-splitters",
        "transformers",
        "tokenizers",
        "tiktoken",
    ]
    
    # Uninstall conflicting packages
    for package in packages_to_uninstall:
        print(f"Uninstalling {package}...")
        run_command([sys.executable, "-m", "pip", "uninstall", "-y", package], verbose=False)
    
    # First, install langchain-core since langchain depends on it
    print("Installing langchain-core first...")
    success, _ = run_command(
        [sys.executable, "-m", "pip", "install", f"langchain-core=={compatible_versions['langchain-core']}"],
        verbose=True
    )
    if not success:
        print_error("Failed to install langchain-core. Dependency resolution may fail.")
    
    # Then install the rest
    for package, version in compatible_versions.items():
        if package == "langchain-core":
            continue  # Already installed
        print(f"Installing {package}=={version}...")
        success, _ = run_command(
            [sys.executable, "-m", "pip", "install", f"{package}=={version}"],
            verbose=False
        )
        if success:
            print_success(f"Installed {package} {version}")
        else:
            print_warning(f"Failed to install {package} {version}")
    
    # Update requirements.txt
    update_requirements_file(compatible_versions)
    
    return True

def update_requirements_file(compatible_versions):
    """Update requirements.txt with compatible versions."""
    print("Updating requirements.txt...")
    
    req_file = PROJECT_ROOT / "requirements.txt"
    fixed_req_file = PROJECT_ROOT / "requirements.fixed.txt"
    
    # Create fixed requirements file
    with open(fixed_req_file, "w") as f:
        f.write("# LawGlance Fixed Requirements\n")
        f.write("# These package versions are compatible with each other and resolve dependency conflicts\n\n")
        
        # Core dependencies
        f.write("# Core packages\n")
        f.write(f"langchain-core=={compatible_versions['langchain-core']}\n")
        f.write(f"langchain=={compatible_versions['langchain']}\n")
        f.write("langchain-openai==0.0.2\n")
        f.write("openai==1.9.0\n\n")
        
        # Text processing
        f.write("# Text processing and tokenization\n")
        f.write(f"tiktoken=={compatible_versions['tiktoken']}\n")
        f.write(f"tokenizers=={compatible_versions['tokenizers']}\n")
        f.write(f"transformers=={compatible_versions['transformers']}\n\n")
        
        # UI
        f.write("# Streamlit UI\n")
        f.write("streamlit==1.30.0\n")
        f.write("streamlit-chat==0.1.1\n\n")
        
        # DB
        f.write("# Vector database\n")
        f.write("chromadb==0.4.22\n")
        f.write("langchain-chroma==0.0.2\n\n")
        
        # Document processing
        f.write("# Document processing\n")
        f.write("pypdf==3.17.4\n")
        f.write("python-docx==1.0.1\n\n")
        
        # Utilities
        f.write("# Utilities\n")
        f.write(f"python-dotenv=={compatible_versions['python-dotenv']}\n")
        f.write("pydantic==2.5.3\n")
        f.write("tqdm==4.66.1\n\n")
        
        # Build dependencies
        f.write("# Build dependencies\n")
        f.write("pyinstaller==6.2.0\n")
        f.write("pillow==10.1.0\n")
    
    print_success(f"Created fixed requirements file at {fixed_req_file}")
    
    # Create backup of current requirements.txt if it exists
    if req_file.exists():
        backup_file = req_file.with_suffix(".txt.bak")
        shutil.copy2(req_file, backup_file)
        print_success(f"Backed up original requirements to {backup_file}")
        
        # Copy fixed requirements to requirements.txt
        shutil.copy2(fixed_req_file, req_file)
        print_success(f"Updated {req_file} with fixed dependencies")
    else:
        shutil.copy2(fixed_req_file, req_file)
        print_success(f"Created new {req_file} with fixed dependencies")

def create_or_fix_app_py():
    """Create or fix app.py file."""
    print_header("Checking app.py")
    
    app_path = PROJECT_ROOT / "app.py"
    
    if not app_path.exists():
        print("Creating app.py...")
        with open(app_path, "w") as f:
            f.write("""# filepath: {0}
\"\"\"Streamlit UI for LawGlance legal assistant.\"\"\"
import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    \"\"\"Main function to run the application.\"\"\"
    # Load environment variables
    load_dotenv()
    
    # Set page configuration
    st.set_page_config(page_title="LawGlance", page_icon="📖", layout="wide")
    
    # Main title
    st.title("LawGlance Legal Assistant")
    st.write("Welcome to LawGlance, your AI-powered legal assistant.")
    
    # Simple input area
    user_input = st.text_area("Enter your legal question:", height=100)
    
    if st.button("Submit"):
        if user_input:
            st.write("Processing your question...")
            # Placeholder for actual processing
            st.write(f"Answer: This is a placeholder response to: '{{user_input}}'")
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    main()
""".format(app_path))
        print_success(f"Created app.py with a simple Streamlit UI")
    else:
        print(f"app.py already exists, skipping creation")
    
    return True

def create_env_example():
    """Create .env.example file."""
    print_header("Creating .env.example")
    
    env_example_path = PROJECT_ROOT / ".env.example"
    env_path = PROJECT_ROOT / ".env"
    
    with open(env_example_path, "w") as f:
        f.write("""# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Vector Store Configuration 
# VECTOR_STORE_DIR=chroma_db_legal_bot_part1

# Optional: Model Configuration
# MODEL_NAME=gpt-4o-mini
# MODEL_TEMPERATURE=0.9
""")
    
    print_success(f"Created .env.example")
    
    # Create .env if it doesn't exist
    if not env_path.exists():
        shutil.copy2(env_example_path, env_path)
        print_success(f"Created .env file (update with your actual API key)")
    
    return True

def create_basic_directories():
    """Create basic directory structure with placeholder files."""
    print_header("Creating Basic Directory Structure")
    
    # Create src directory and __init__.py
    src_dir = PROJECT_ROOT / "src"
    src_dir.mkdir(exist_ok=True)
    
    with open(src_dir / "__init__.py", "w") as f:
        f.write('"""LawGlance main package."""\n')
    
    # Create data directory with placeholder README
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "README.md", "w") as f:
        f.write("""# Data Directory

This directory contains sample documents and data files for LawGlance.

## Contents

- Sample legal documents
- Training data
- Test documents

*Add your documents to this directory to use them with LawGlance.*
""")
    
    return True

def main():
    """Main repair function."""
    print_header("LawGlance Project Repair Tool")
    
    print("This tool will repair the entire LawGlance project by:")
    print("1. Fixing build_desktop_app.py")
    print("2. Resolving dependency conflicts")
    print("3. Creating necessary files and directories")
    print("4. Ensuring icon paths are correct")
    print("5. Setting up a proper environment for building")
    print("")
    
    # Ask for confirmation
    confirm = input("Continue with the repair process? (y/n): ")
    if confirm.lower() != 'y':
        print("Repair cancelled.")
        return
    
    # Check Python environment
    if not check_python_environment():
        print_error("Python environment check failed. Please fix these issues and try again.")
        return
    
    # Fix project structure
    fix_project_structure()
    
    # Fix logo files
    fix_logo()
    
    # Fix build_desktop_app.py
    fix_build_desktop_app()
    
    # Create or fix app.py
    create_or_fix_app_py()
    
    # Create .env.example
    create_env_example()
    
    # Create basic directories
    create_basic_directories()
    
    # Fix dependencies
    fix_dependencies()
    
    print_header("Repair Process Complete!")
    print("")
    print("Your LawGlance project has been repaired and is ready to build.")
    print("")
    print("Next steps:")
    print("1. Update the .env file with your actual API keys")
    print("2. Run the build script: python build_desktop_app.py")
    print("3. Choose option 1 to build the executable")
    print("")
    
    # Offer to run build immediately
    build_now = input("Would you like to build the executable now? (y/n): ")
    if build_now.lower() == 'y':
        print("")
        print("Running build_desktop_app.py...")
        subprocess.check_call([sys.executable, "build_desktop_app.py"])
    else:
        print("Exiting. Run 'python build_desktop_app.py' when you're ready to build.")

if __name__ == "__main__":
    main()
