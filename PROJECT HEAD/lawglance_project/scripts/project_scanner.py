"""
Project Scanner and Repair Tool for LawGlance.

This script analyzes the project structure, identifies common issues,
and fixes them when possible. It's especially useful before attempting
to build the executable to ensure all dependencies are met and files
are correctly configured.
"""
import os
import sys
import re
import subprocess
import importlib.util
import json
import shutil
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# Define project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class ProjectScanner:
    """Project scanner and repair tool for Python projects."""

    def __init__(self, project_path: Path):
        """Initialize the scanner with project path."""
        self.project_path = project_path
        self.issues_found = 0
        self.issues_fixed = 0
        self.warnings = 0
        
        # Define required directories and files
        self.required_dirs = ['src', 'logo', 'data']
        self.required_files = ['app.py', 'requirements.txt']
        
        # Define commonly missed dependencies
        self.common_dependencies = {
            'streamlit': 'streamlit>=1.24.0',
            'langchain': 'langchain>=0.0.267',
            'openai': 'openai>=1.3.0',
            'langchain_openai': 'langchain-openai>=0.0.2',
            'pypdf': 'pypdf>=3.15.1',
            'python-dotenv': 'python-dotenv>=1.0.0',
            'pillow': 'pillow>=9.5.0',
        }
        
        # PyInstaller dependencies
        self.build_dependencies = {
            'pyinstaller': 'pyinstaller>=5.13.0',
        }
        
        # Environment variables needed
        self.env_vars = ['OPENAI_API_KEY']

    def scan_project(self) -> bool:
        """
        Scan the project for common issues and fix them if possible.
        
        Returns:
            bool: True if the project is ready for building, False otherwise.
        """
        print("\n" + "=" * 60)
        print("LawGlance Project Scanner and Repair Tool".center(60))
        print("=" * 60)
        
        print(f"\nAnalyzing project at: {self.project_path}")
        
        # Check project structure
        self._check_project_structure()
        
        # Check Python environment
        self._check_python_environment()
        
        # Check for required files
        self._check_required_files()
        
        # Check dependencies
        self._check_dependencies()
        
        # Check environment variables
        self._check_environment_variables()
        
        # Check for PyInstaller issues
        self._check_pyinstaller_issues()
        
        # Check build script
        self._check_build_script()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Scan Results".center(60))
        print("=" * 60)
        print(f"Issues found: {self.issues_found}")
        print(f"Issues fixed: {self.issues_fixed}")
        print(f"Warnings: {self.warnings}")
        
        if self.issues_found == self.issues_fixed:
            print("\n✅ Project is ready for building!")
            return True
        else:
            print(f"\n⚠️ Project has unresolved issues: {self.issues_found - self.issues_fixed} remaining")
            return False

    def _check_project_structure(self):
        """Check if project has the required directory structure."""
        print("\nChecking project structure...")
        
        # Check required directories
        for dir_name in self.required_dirs:
            dir_path = self.project_path / dir_name
            if not dir_path.exists():
                self.issues_found += 1
                print(f"  ❌ Missing directory: {dir_name}")
                
                # Create directory
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"  ✅ Created directory: {dir_name}")
                    self.issues_fixed += 1
                except Exception as e:
                    print(f"  ⚠️ Could not create directory {dir_name}: {str(e)}")
            else:
                print(f"  ✓ Directory exists: {dir_name}")

    def _check_required_files(self):
        """Check if project has required files."""
        print("\nChecking required files...")
        
        # Check required files
        for file_name in self.required_files:
            file_path = self.project_path / file_name
            if not file_path.exists():
                self.issues_found += 1
                print(f"  ❌ Missing file: {file_name}")
                
                # Create basic files if needed
                if file_name == "app.py":
                    self._create_app_py()
                elif file_name == "requirements.txt":
                    self._create_requirements_txt()
            else:
                print(f"  ✓ File exists: {file_name}")
        
        # Check for .env or .env.example
        if not (self.project_path / ".env").exists():
            if not (self.project_path / ".env.example").exists():
                self.issues_found += 1
                print(f"  ❌ Missing file: .env or .env.example")
                self._create_env_example()
            else:
                print("  ⚠️ Found .env.example but no .env file (this is OK for development)")
                self.warnings += 1
        else:
            print("  ✓ File exists: .env")

    def _check_python_environment(self):
        """Check Python environment for issues."""
        print("\nChecking Python environment...")
        
        # Check Python version
        py_version = platform.python_version_tuple()
        py_version_str = platform.python_version()
        if int(py_version[0]) < 3 or (int(py_version[0]) == 3 and int(py_version[1]) < 8):
            self.issues_found += 1
            print(f"  ❌ Python 3.8+ required, found {py_version_str}")
        else:
            print(f"  ✓ Python version: {py_version_str}")
        
        # Check if running in virtual environment
        in_venv = sys.prefix != sys.base_prefix
        if not in_venv:
            print("  ⚠️ Not running in a virtual environment (recommended)")
            self.warnings += 1
        else:
            print("  ✓ Running in virtual environment")

    def _check_dependencies(self):
        """Check if required dependencies are installed and in requirements.txt."""
        print("\nChecking dependencies...")
        
        # Read requirements.txt if it exists
        req_file = self.project_path / "requirements.txt"
        requirements = set()
        
        if req_file.exists():
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name without version
                        match = re.match(r'^([a-zA-Z0-9_\-\.]+)', line)
                        if match:
                            requirements.add(match.group(1).lower())
        
        # Check for common dependencies in requirements.txt
        missing_requirements = []
        for dep, spec in self.common_dependencies.items():
            if dep.lower() not in requirements:
                self.issues_found += 1
                print(f"  ❌ Missing dependency in requirements.txt: {dep}")
                missing_requirements.append(spec)
        
        # Add missing requirements to requirements.txt
        if missing_requirements:
            try:
                with open(req_file, "a") as f:
                    f.write("\n# Added by project scanner\n")
                    for req in missing_requirements:
                        f.write(f"{req}\n")
                print(f"  ✅ Added {len(missing_requirements)} missing dependencies to requirements.txt")
                self.issues_fixed += len(missing_requirements)
            except Exception as e:
                print(f"  ⚠️ Could not update requirements.txt: {str(e)}")
        
        # Check if build dependencies are installed
        for dep in self.build_dependencies:
            try:
                importlib.import_module(dep)
                print(f"  ✓ Build dependency installed: {dep}")
            except ImportError:
                self.issues_found += 1
                print(f"  ❌ Missing build dependency: {dep}")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                    print(f"  ✅ Installed build dependency: {dep}")
                    self.issues_fixed += 1
                except Exception as e:
                    print(f"  ⚠️ Could not install {dep}: {str(e)}")

    def _check_environment_variables(self):
        """Check for required environment variables."""
        print("\nChecking environment variables...")
        
        # Check if .env file exists
        env_file = self.project_path / ".env"
        env_example_file = self.project_path / ".env.example"
        
        if env_file.exists():
            env_vars = {}
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
                        except ValueError:
                            pass
            
            # Check required environment variables
            for var in self.env_vars:
                if var not in env_vars:
                    self.issues_found += 1
                    print(f"  ❌ Missing environment variable in .env: {var}")
                elif env_vars[var] in ('your_api_key_here', 'your_openai_api_key_here', ''):
                    self.issues_found += 1
                    print(f"  ❌ Environment variable not set properly: {var}")
                else:
                    print(f"  ✓ Environment variable set: {var}")
        elif env_example_file.exists():
            print("  ⚠️ No .env file found, but .env.example exists")
            self.warnings += 1
        else:
            self.issues_found += 1
            print("  ❌ No .env or .env.example file found")

    def _check_pyinstaller_issues(self):
        """Check for common PyInstaller issues."""
        print("\nChecking for PyInstaller issues...")
        
        # Check if logo directory exists
        logo_dir = self.project_path / "logo"
        if logo_dir.exists():
            # Check if logo.ico exists
            icon_path = logo_dir / "logo.ico"
            if not icon_path.exists():
                self.issues_found += 1
                print("  ❌ Missing logo.ico file for PyInstaller")
                
                # Check if we can create it from logo.png
                png_path = logo_dir / "logo.png"
                if png_path.exists():
                    try:
                        from PIL import Image
                        img = Image.open(png_path)
                        img.save(icon_path, sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
                        print("  ✅ Created logo.ico from logo.png")
                        self.issues_fixed += 1
                    except Exception as e:
                        print(f"  ⚠️ Could not create logo.ico: {str(e)}")
                else:
                    # Try to create a basic logo
                    self._create_basic_logo()
        else:
            print("  ⚠️ Logo directory does not exist, can't check for ico file")
    
    def _check_build_script(self):
        """Check build script for issues."""
        print("\nChecking build script...")
        
        build_script = self.project_path / "build_desktop_app.py"
        if build_script.exists():
            print("  ✓ Build script exists: build_desktop_app.py")
            
            # Read script content to check for common issues
            with open(build_script, "r") as f:
                content = f.read()
                
                # Check if icon path is specified correctly
                if "icon=" in content and "path/to/icon.ico" in content:
                    self.issues_found += 1
                    print("  ❌ Build script contains placeholder icon path")
                    
                    # Try to fix the path
                    fixed_content = content.replace("path/to/icon.ico", "logo/logo.ico")
                    try:
                        with open(build_script, "w") as f_out:
                            f_out.write(fixed_content)
                        print("  ✅ Fixed icon path in build script")
                        self.issues_fixed += 1
                    except Exception as e:
                        print(f"  ⚠️ Could not fix build script: {str(e)}")
        else:
            self.issues_found += 1
            print("  ❌ Missing build script: build_desktop_app.py")
            self._create_build_script()
    
    def _create_app_py(self):
        """Create a basic app.py file."""
        app_content = """
\"\"\"Streamlit UI for LawGlance legal assistant.\"\"\"
import os
import sys
import random
import time
import base64
from typing import Iterator, Optional

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(page_title="LawGlance", page_icon="📖", layout="wide")

def main():
    \"\"\"Main function for the LawGlance application.\"\"\"
    st.title("LawGlance - Legal Assistant")
    st.write("Welcome to LawGlance, your AI-powered legal assistant.")
    
    # Simple example input
    user_input = st.text_area("Enter your legal question:", height=100)
    
    if st.button("Submit"):
        if user_input:
            st.write("Processing your question...")
            # Placeholder for actual processing
            st.write(f"Answer: This is a placeholder response to: '{user_input}'")
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    main()
"""
        try:
            with open(self.project_path / "app.py", "w") as f:
                f.write(app_content)
            print(f"  ✅ Created basic app.py file")
            self.issues_fixed += 1
        except Exception as e:
            print(f"  ⚠️ Could not create app.py: {str(e)}")

    def _create_requirements_txt(self):
        """Create a requirements.txt file with common dependencies."""
        requirements_content = "# LawGlance requirements\n"
        
        # Add all common dependencies
        for _, spec in self.common_dependencies.items():
            requirements_content += f"{spec}\n"
        
        # Add build dependencies
        requirements_content += "\n# Build dependencies\n"
        for _, spec in self.build_dependencies.items():
            requirements_content += f"{spec}\n"
        
        try:
            with open(self.project_path / "requirements.txt", "w") as f:
                f.write(requirements_content)
            print(f"  ✅ Created requirements.txt with common dependencies")
            self.issues_fixed += 1
        except Exception as e:
            print(f"  ⚠️ Could not create requirements.txt: {str(e)}")

    def _create_env_example(self):
        """Create a .env.example file."""
        env_content = """# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Vector Store Configuration 
VECTOR_STORE_DIR=chroma_db_legal_bot_part1

# Model Configuration
MODEL_NAME=gpt-4o-mini
MODEL_TEMPERATURE=0.9
"""
        try:
            with open(self.project_path / ".env.example", "w") as f:
                f.write(env_content)
            print(f"  ✅ Created .env.example file")
            self.issues_fixed += 1
            
            # Also create a .env file with placeholder values
            with open(self.project_path / ".env", "w") as f:
                f.write(env_content)
            print(f"  ✅ Created .env file with placeholder values (update with your API key)")
        except Exception as e:
            print(f"  ⚠️ Could not create .env files: {str(e)}")

    def _create_basic_logo(self):
        """Create a basic logo for the project."""
        try:
            from PIL import Image, ImageDraw
            
            # Create logo directory if it doesn't exist
            logo_dir = self.project_path / "logo"
            logo_dir.mkdir(exist_ok=True)
            
            # Create a blue background with scales of justice
            img = Image.new('RGB', (256, 256), color=(33, 150, 243))
            draw = ImageDraw.Draw(img)
            
            # Draw scales of justice in white (simple geometry)
            # Horizontal bar
            draw.rectangle([64, 170, 192, 192], fill=(255, 255, 255))
            # Vertical stand
            draw.rectangle([118, 64, 138, 170], fill=(255, 255, 255))
            # Left scale
            draw.ellipse([64, 64, 114, 114], outline=(255, 255, 255), width=10)
            # Right scale
            draw.ellipse([162, 64, 212, 114], outline=(255, 255, 255), width=10)
            
            # Save as PNG
            img.save(logo_dir / "logo.png")
            
            # Save as ICO for Windows
            img.save(logo_dir / "logo.ico", sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
            
            print("  ✅ Created basic logo files (logo.png and logo.ico)")
            self.issues_fixed += 1
        except ImportError:
            print("  ⚠️ Pillow not installed, cannot create logo")
            self.warnings += 1
        except Exception as e:
            print(f"  ⚠️ Could not create logo: {str(e)}")

    def _create_build_script(self):
        """Create a basic build_desktop_app.py script."""
        build_script_content = """
\"\"\"
Build script for creating the LawGlance desktop application.
Handles icon creation and PyInstaller configuration correctly.
\"\"\"
import os
import sys
import subprocess
from pathlib import Path
import PyInstaller.__main__

# Define project directory
PROJECT_ROOT = Path(__file__).parent

def create_logo():
    \"\"\"Create a logo if one doesn't exist, and return the path to the icon file.\"\"\"
    logo_dir = PROJECT_ROOT / "logo"
    logo_dir.mkdir(exist_ok=True)
    
    icon_path = logo_dir / "logo.ico"
    png_path = logo_dir / "logo.png"
    
    # If icon already exists, return its path
    if icon_path.exists():
        print(f"Using existing icon at {icon_path}")
        return icon_path
    
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
        print(f"Created logo image at {png_path}")
        
        # Save as ICO for Windows
        img.save(icon_path, sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print(f"Created icon at {icon_path}")
        
        return icon_path
    
    except ImportError:
        print("Warning: PIL/Pillow not installed. Cannot create logo.")
        print("Installing Pillow...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            print("Pillow installed. Retrying logo creation...")
            return create_logo()  # Try again
        except Exception as e:
            print(f"Error installing Pillow: {str(e)}")
            return None
    
    except Exception as e:
        print(f"Error creating logo: {str(e)}")
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
        cmd.append(f'--icon={icon_path}')
    
    # Add required hidden imports for streamlit
    cmd.extend([
        '--hidden-import=streamlit.web.bootstrap',
        '--hidden-import=streamlit.runtime.scriptrunner',
        '--hidden-import=langchain',
        '--hidden-import=langchain_openai',
    ])
    
    # Add data folders
    cmd.extend([
        '--add-data', f'logo{os.pathsep}logo',
    ])
    
    # Add the main script to build
    cmd.append('app.py')
    
    # Run PyInstaller
    try:
        PyInstaller.__main__.run(cmd)
        print("Executable built successfully.")
        return True
    except Exception as e:
        print(f"Error building executable: {str(e)}")
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
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=LawGlance-Setup
SetupIconFile=logo\\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\\LawGlance\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon
\"\"\")
    
    # Run Inno Setup
    try:
        subprocess.check_call([inno_setup_path, str(iss_file)])
        print("Installer created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating installer: {str(e)}")
        return False
    except FileNotFoundError:
        print(f"Inno Setup executable not found at {inno_setup_path}")
        return False

def create_portable():
    \"\"\"Create a portable ZIP version.\"\"\"
    print("Generating portable version...")
    
    import shutil
    
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
        zip_path = output_dir / "LawGlance-Portable"
        shutil.make_archive(str(zip_path), 'zip', exe_dir)
        print(f"Portable version created at {zip_path}.zip")
        return True
    except Exception as e:
        print(f"Error creating portable version: {str(e)}")
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
        try:
            with open(self.project_path / "build_desktop_app.py", "w") as f:
                f.write(build_script_content.strip())
            print(f"  ✅ Created build_desktop_app.py script")
            self.issues_fixed += 1
        except Exception as e:
            print(f"  ⚠️ Could not create build script: {str(e)}")


def main():
    """Run the project scanner."""
    scanner = ProjectScanner(PROJECT_ROOT)
    scanner.scan_project()


if __name__ == "__main__":
    main()
