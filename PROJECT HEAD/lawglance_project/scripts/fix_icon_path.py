"""
Fix Icon Path Script for LawGlance

This script fixes issues with the icon path in build_desktop_app.py
and ensures the logo exists for PyInstaller to use.
"""
import os
import sys
from pathlib import Path

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def fix_build_script():
    """Fix the build_desktop_app.py script to use absolute paths."""
    build_script_path = PROJECT_ROOT / "build_desktop_app.py"
    
    if not build_script_path.exists():
        print(f"Error: build_desktop_app.py not found at {build_script_path}")
        return False
    
    print(f"Reading build script from {build_script_path}")
    
    # Read the current content
    with open(build_script_path, "r") as f:
        content = f.read()
    
    # Create a backup
    with open(str(build_script_path) + ".bak", "w") as f:
        f.write(content)
    print(f"Created backup at {build_script_path}.bak")
    
    # Update the script
    fixed_content = """
# filepath: /C:/Users/casey/Desktop/lawglance_project/build_desktop_app.py
\"\"\"
Build script for creating the LawGlance desktop application.
This fixed version uses absolute paths to avoid path resolution issues.
\"\"\"
import os
import sys
import subprocess
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
        print(f"Using existing icon at {icon_path}")
        return str(icon_path.absolute())
    
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
        
        return str(icon_path.absolute())
    
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
    
    # Add icon if one was created (using absolute path)
    if icon_path:
        cmd.append(f'--icon={icon_path}')
    
    # Add required hidden imports for streamlit
    cmd.extend([
        '--hidden-import=streamlit.web.bootstrap',
        '--hidden-import=streamlit.runtime.scriptrunner',
        '--hidden-import=langchain',
        '--hidden-import=langchain_openai',
    ])
    
    # Add data folders (using absolute paths)
    logo_dir = PROJECT_ROOT / "logo"
    if logo_dir.exists():
        cmd.extend([
            '--add-data', f'{logo_dir}{os.pathsep}logo',
        ])
    
    # Add the main script to build (using absolute path)
    app_path = PROJECT_ROOT / "app.py"
    cmd.append(str(app_path))
    
    # Run PyInstaller
    try:
        PyInstaller.__main__.run(cmd)
        print("Executable built successfully.")
        return True
    except Exception as e:
        print(f"Error building executable: {str(e)}")
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

    # Write the fixed content
    with open(build_script_path, "w") as f:
        f.write(fixed_content)
    
    print(f"Fixed build script at {build_script_path}")
    return True

def create_logo():
    """Create a logo file if it doesn't exist."""
    logo_dir = PROJECT_ROOT / "logo"
    logo_dir.mkdir(exist_ok=True)
    
    icon_path = logo_dir / "logo.ico"
    png_path = logo_dir / "logo.png"
    
    if icon_path.exists():
        print(f"Icon already exists at {icon_path}")
        return True
    
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple logo
        print("Creating logo files...")
        img = Image.new('RGB', (256, 256), color=(33, 150, 243))
        draw = ImageDraw.Draw(img)
        
        # Draw scales of justice
        draw.rectangle([64, 170, 192, 192], fill=(255, 255, 255))
        draw.rectangle([118, 64, 138, 170], fill=(255, 255, 255))
        draw.ellipse([64, 64, 114, 114], outline=(255, 255, 255), width=10)
        draw.ellipse([162, 64, 212, 114], outline=(255, 255, 255), width=10)
        
        # Save as PNG
        img.save(png_path)
        print(f"Created PNG logo at {png_path}")
        
        # Save as ICO
        img.save(icon_path, sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print(f"Created ICO logo at {icon_path}")
        
        return True
    except ImportError:
        print("Pillow not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
            return create_logo()  # Try again after installing
        except Exception as e:
            print(f"Error installing Pillow: {str(e)}")
            return False
    except Exception as e:
        print(f"Error creating logo: {str(e)}")
        return False

if __name__ == "__main__":
    print("LawGlance - Icon Path Fixer")
    print("==========================")
    
    # Create logo if needed
    if not create_logo():
        print("Failed to create logo files.")
        sys.exit(1)
    
    # Fix build script
    if not fix_build_script():
        print("Failed to fix build script.")
        sys.exit(1)
    
    print("\nFix complete! You can now run build_desktop_app.py to build your executable.")
