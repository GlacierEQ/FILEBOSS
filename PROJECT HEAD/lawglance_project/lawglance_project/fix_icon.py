"""
Quick fix for the PyInstaller icon path issue.

This script:
1. Creates a logo directory in the correct location if it doesn't exist
2. Creates icon files (PNG and ICO) if they don't exist
3. Updates the build_desktop_app.py to use the correct absolute paths
"""
import os
import sys
import subprocess
from pathlib import Path
import shutil

# Project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()

def create_logo_files():
    """Create logo directory and files if they don't exist."""
    logo_dir = PROJECT_ROOT / "logo"
    logo_dir.mkdir(exist_ok=True)
    
    icon_path = logo_dir / "logo.ico"
    png_path = logo_dir / "logo.png"
    
    # If icon already exists, we're good
    if icon_path.exists():
        print(f"✓ Icon already exists at {icon_path}")
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
        print(f"✓ Created PNG logo at {png_path}")
        
        # Save as ICO
        img.save(icon_path, sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print(f"✓ Created ICO logo at {icon_path}")
        
        return icon_path
        
    except Exception as e:
        print(f"❌ Error creating logo: {str(e)}")
        return None

def fix_build_script(icon_path):
    """Update build_desktop_app.py to use absolute paths."""
    build_script_path = PROJECT_ROOT / "build_desktop_app.py"
    
    if not build_script_path.exists():
        print(f"❌ Build script not found at {build_script_path}")
        return False
    
    # Read the current script content
    with open(build_script_path, "r") as f:
        content = f.read()
    
    # Create a backup
    backup_path = str(build_script_path) + ".bak"
    with open(backup_path, "w") as f:
        f.write(content)
    print(f"✓ Created backup at {backup_path}")
    
    # Fix the script
    # Replace relative path with absolute path
    if "--icon=path/to/icon.ico" in content:
        new_content = content.replace("--icon=path/to/icon.ico", f"--icon={icon_path.absolute()}")
        with open(build_script_path, "w") as f:
            f.write(new_content)
        print("✓ Fixed icon path in build script")
    elif "--icon=logo/logo.ico" in content:
        new_content = content.replace("--icon=logo/logo.ico", f"--icon={icon_path.absolute()}")
        with open(build_script_path, "w") as f:
            f.write(new_content)
        print("✓ Fixed icon path in build script")
    else:
        print("⚠️ Could not find icon path in build script to fix")
        print("   Manually update your build script to use the absolute path:")
        print(f"   --icon={icon_path.absolute()}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("LawGlance Icon Path Fix Tool")
    print("=" * 60)
    
    # Step 1: Create logo files
    icon_path = create_logo_files()
    if not icon_path:
        print("❌ Failed to create logo files")
        sys.exit(1)
    
    # Step 2: Fix the build script
    fix_build_script(icon_path)
    
    print("\n" + "=" * 60)
    print("✓ Fix complete!")
    print("=" * 60)
    print("\nNow run your build script again:")
    print(f"python build_desktop_app.py")
    print("\nOr use the direct PyInstaller command:")
    print(f"pyinstaller --onefile --windowed --icon={icon_path.absolute()} app.py --name LawGlance")
    print("=" * 60)
