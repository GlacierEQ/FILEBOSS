#!/usr/bin/env python3
"""
Enhanced build script for creating executable versions of LawGlance.
Provides comprehensive error handling, dependency checking, and user-friendly feedback.
"""
import os
import sys
import shutil
import platform
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
log_file = f"lawglance_build_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LawGlance-Builder")

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGO_DIR = PROJECT_ROOT / "logo"

# Required Python packages
REQUIRED_PACKAGES = [
    "pyinstaller",
    "pillow",
    "setuptools",
    "wheel",
    "streamlit",
    "langchain",
    "langchain-openai",
]

class BuildError(Exception):
    """Custom exception for build errors."""
    pass

def print_banner():
    """Print a nice banner for the builder."""
    print("\n" + "=" * 80)
    print("""
    █▀█ █▀▄ █▀▀   █▀▄ █ █ █ █   █▀▄ █▀▀ █▀█
    █▀▀ █▄▀ █▀▀   █▀▄ █ █ █ █   █▄▀ █▀  █▀▄
    ▀   ▀ ▀ ▀▀▀   ▀▀  ▀▀▀ ▀▀▀   ▀ ▀ ▀▀▀ ▀ ▀
    LawGlance Desktop Application Builder
    """)
    print("=" * 80 + "\n")

def check_environment():
    """Check that the environment meets requirements."""
    logger.info("Checking environment...")
    
    # Check Python version
    py_version = platform.python_version_tuple()
    if int(py_version[0]) < 3 or (int(py_version[0]) == 3 and int(py_version[1]) < 8):
        raise BuildError(f"Python 3.8+ required, found {platform.python_version()}")
    logger.info(f"✓ Python version: {platform.python_version()}")
    
    # Check if we're in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        logger.warning("⚠️ Not running in a virtual environment. This is recommended but not required.")
    else:
        logger.info("✓ Running in virtual environment")
    
    # Check for required files
    required_files = ["app.py", "requirements.txt"]
    for file in required_files:
        if not (PROJECT_ROOT / file).exists():
            raise BuildError(f"Required file {file} not found in project root")
    logger.info("✓ Required project files present")
    
    # Return platform info
    return {
        "os": platform.system(),
        "python_version": platform.python_version(),
        "in_venv": in_venv,
    }

def install_dependencies():
    """Install required dependencies."""
    logger.info("Installing required build dependencies...")
    
    for package in REQUIRED_PACKAGES:
        try:
            logger.info(f"Checking {package}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", package],
                stdout=subprocess.DEVNULL
            )
            logger.info(f"✓ {package} installed/updated")
        except subprocess.CalledProcessError as e:
            raise BuildError(f"Failed to install {package}: {str(e)}")
    
    # Install project requirements
    try:
        logger.info("Installing project requirements...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")],
            stdout=subprocess.DEVNULL
        )
        logger.info("✓ Project requirements installed")
    except subprocess.CalledProcessError as e:
        raise BuildError(f"Failed to install project requirements: {str(e)}")

def ensure_logo_exists():
    """Make sure we have a logo/icon for the application."""
    LOGO_DIR.mkdir(exist_ok=True)
    logo_path = LOGO_DIR / "logo.png"
    icon_path = LOGO_DIR / "logo.ico"
    
    # Skip if ico already exists
    if icon_path.exists():
        logger.info("✓ Logo icon already exists")
        return icon_path
    
    # Create logo if png doesn't exist
    if not logo_path.exists():
        logger.info("Creating logo...")
        try:
            # Try to import the placeholder logo creation function
            spec_file = LOGO_DIR / "create_placeholder_logo.py"
            
            # If the script doesn't exist, create it
            if not spec_file.exists():
                logger.info("Creating logo generation script...")
                with open(spec_file, 'w') as f:
                    f.write("""
\"\"\"Create a placeholder logo for LawGlance.\"\"\"
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_logo():
    \"\"\"Create a placeholder logo for LawGlance.\"\"\"
    logo_dir = Path(__file__).parent
    logo_dir.mkdir(exist_ok=True)
    
    logo_path = logo_dir / "logo.png"
    icon_path = logo_dir / "logo.ico"
    
    if logo_path.exists():
        return
    
    img_size = (512, 512)
    img = Image.new('RGBA', img_size, color=(33, 150, 243, 255))  # Blue background
    draw = ImageDraw.Draw(img)
    
    try:
        font_size = 72
        try:
            font = ImageFont.truetype("Arial Bold.ttf", font_size)
        except:
            font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "LawGlance"
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (200, 40)
    position = ((img_size[0] - text_width) // 2, (img_size[1] - text_height) // 2)
    
    # Add a legal scale symbol
    draw.rectangle([156, 340, 356, 360], fill=(255, 255, 255, 255))
    draw.rectangle([246, 240, 266, 340], fill=(255, 255, 255, 255))
    draw.ellipse([196, 190, 246, 240], outline=(255, 255, 255, 255), width=10)
    draw.ellipse([266, 190, 316, 240], outline=(255, 255, 255, 255), width=10)
    
    draw.text(position, text, font=font, fill=(255, 255, 255, 255))
    
    img.save(logo_path, 'PNG')
    print(f"Created logo at {logo_path}")
    
    if not icon_path.exists():
        img.save(icon_path, format='ICO', sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
        print(f"Created icon at {icon_path}")

if __name__ == "__main__":
    create_placeholder_logo()
""")
            
            # Import and run the logo creation function
            import importlib.util
            spec = importlib.util.spec_from_file_location("create_placeholder_logo", spec_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.create_placeholder_logo()
            
            logger.info("✓ Logo created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not create logo: {e}")
            logger.info("Continuing without icon...")
            return None
    
    # Convert PNG to ICO if needed
    if logo_path.exists() and not icon_path.exists():
        logger.info("Converting logo.png to icon...")
        try:
            from PIL import Image
            img = Image.open(logo_path)
            img.save(icon_path, format='ICO', sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
            logger.info("✓ Icon created successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not convert logo to icon: {e}")
            logger.info("Continuing without icon...")
            return None
    
    return icon_path

def build_executable(args):
    """Build executable using PyInstaller."""
    logger.info("Building executable...")
    
    # Ensure icon exists
    icon_path = ensure_logo_exists()
    
    # Determine whether to use onefile or onedir
    onefile = "--onefile" if args.onefile else ""
    
    # Determine console mode
    console = "" if args.console else "--windowed"
    
    # Construct command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        onefile,
        console,
        "--name=LawGlance"
    ]
    
    # Add icon if available
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    # Add data files
    cmd.extend([
        "--add-data", f"logo{os.pathsep}logo",
        "--add-data", f".env{os.pathsep}.",
        "--add-data", f"data{os.pathsep}data",
    ])
    
    # Add hidden imports
    cmd.extend([
        "--hidden-import=streamlit.web.bootstrap",
        "--hidden-import=streamlit.runtime.scriptrunner",
        "--hidden-import=langchain",
        "--hidden-import=langchain_openai",
        "--hidden-import=langchain_chroma",
    ])
    
    # Add main script
    cmd.append("app.py")
    
    # Filter out empty arguments
    cmd = [arg for arg in cmd if arg]
    
    # Run PyInstaller
    try:
        logger.info(f"Running PyInstaller with args: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        logger.info("✓ Executable build completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ PyInstaller build failed: {e}")
        raise BuildError("PyInstaller build failed")

def build_installer(args):
    """Build installer using Inno Setup."""
    logger.info("Building installer...")
    
    # Check if Inno Setup is installed
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    inno_path = None
    for path in inno_paths:
        if os.path.exists(path):
            inno_path = path
            break
    
    if not inno_path:
        logger.warning("⚠️ Inno Setup not found. Installer cannot be created.")
        logger.info("Download Inno Setup from: https://jrsoftware.org/isdl.php")
        return False
    
    # Check if installer script exists
    iss_path = PROJECT_ROOT / "installer.iss"
    if not iss_path.exists():
        logger.info("Creating Inno Setup script...")
        with open(iss_path, 'w') as f:
            f.write(f"""
; Inno Setup Script for LawGlance
; Creates a Windows installer for the LawGlance application

#define MyAppName "LawGlance"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "LawGlance"
#define MyAppURL "https://www.lawglance.com"
#define MyAppExeName "LawGlance.exe"

[Setup]
AppId={{{{{guid()}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
DisableProgramGroupPage=yes
; LicenseFile=LICENSE
OutputDir=build\\installer
OutputBaseFilename=LawGlance-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=logo\\logo.ico

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

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
""")
    
    # Create build/installer directory
    installer_dir = BUILD_DIR / "installer"
    installer_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Inno Setup compiler
    try:
        logger.info(f"Running Inno Setup compiler: {inno_path} {iss_path}")
        subprocess.check_call([inno_path, str(iss_path)])
        logger.info("✓ Installer build completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Installer build failed: {e}")
        raise BuildError("Installer build failed")

def create_portable_package(args):
    """Create a portable ZIP version of the application."""
    logger.info("Creating portable package...")
    
    # Make sure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Check if dist directory exists
    dist_lawglance_dir = DIST_DIR / "LawGlance"
    if not dist_lawglance_dir.exists():
        logger.warning("⚠️ dist/LawGlance directory not found. Run executable build first.")
        return False
    
    # Create portable ZIP
    try:
        import shutil
        zip_path = OUTPUT_DIR / "LawGlance-Portable"
        
        # Remove existing zip if it exists
        if (zip_path.with_suffix(".zip")).exists():
            os.remove(zip_path.with_suffix(".zip"))
            
        shutil.make_archive(
            str(zip_path), 
            'zip', 
            DIST_DIR,
            'LawGlance'
        )
        logger.info(f"✓ Portable ZIP created at {zip_path.with_suffix('.zip')}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create portable package: {e}")
        raise BuildError("Portable package creation failed")

def create_webview_app(args):
    """Create a PyWebView-based desktop application."""
    logger.info("Creating PyWebView desktop application...")
    
    # Create the desktop directory if it doesn't exist
    desktop_dir = PROJECT_ROOT / "src" / "desktop"
    desktop_dir.mkdir(exist_ok=True, parents=True)
    
    # Create the webview_app.py file
    webview_file = desktop_dir / "webview_app.py"
    
    if not webview_file.exists():
        logger.info("Creating PyWebView application script...")
        with open(webview_file, 'w') as f:
            f.write("""\"\"\"
Desktop application wrapper for LawGlance.
This module uses PyWebView to create a desktop application that wraps the Streamlit web app.
\"\"\"
import os
import sys
import time
import signal
import atexit
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("lawglance_desktop.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LawGlance-Desktop")

def start_webview_app():
    \"\"\"Entry point for starting the webview app.\"\"\"
    app = LawGlanceApp()
    app.run()
    return app

# Try to import webview, install if not found
try:
    import webview
except ImportError:
    logger.info("PyWebView not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
    import webview

# Determine the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent
STREAMLIT_PORT = 8501

class LawGlanceApp:
    \"\"\"Desktop application wrapper for LawGlance.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the desktop application.\"\"\"
        self.streamlit_process = None
        self.window = None
    
    def start_streamlit_server(self) -> subprocess.Popen:
        \"\"\"
        Start the Streamlit server for the LawGlance application.
        
        Returns:
            The Streamlit server process
        \"\"\"
        logger.info("Starting Streamlit server...")
        env = os.environ.copy()
        
        # Ensure Python path includes our project
        python_path = str(ROOT_DIR)
        if "PYTHONPATH" in env:
            python_path = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = python_path
        
        # Start Streamlit server
        try:
            # On Windows, hide the console window
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
                
            proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", 
                 str(ROOT_DIR / "app.py"),
                 "--server.port", str(STREAMLIT_PORT),
                 "--browser.serverAddress", "localhost",
                 "--server.headless", "true",
                 "--server.enableCORS", "false",
                 "--server.enableXsrfProtection", "false"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            
            logger.info(f"Streamlit server started with PID {proc.pid}")
            return proc
            
        except Exception as e:
            logger.error(f"Error starting Streamlit: {e}")
            raise
    
    def wait_for_streamlit(self, timeout=30) -> bool:
        \"\"\"
        Wait for Streamlit server to start and be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if Streamlit is ready, False otherwise
        \"\"\"
        import socket
        import time
        
        logger.info(f"Waiting for Streamlit to start on port {STREAMLIT_PORT}...")
        
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                # Try to connect to the Streamlit port
                with socket.create_connection(("localhost", STREAMLIT_PORT), timeout=1):
                    logger.info("Streamlit is running!")
                    return True
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(1)
        
        logger.error(f"Timed out waiting for Streamlit after {timeout} seconds")
        return False
    
    def create_window(self) -> None:
        \"\"\"Create and configure the application window.\"\"\"
        logger.info("Creating application window...")
        
        # Load custom CSS for the webview
        js_api = {
            'exit': self.terminate
        }
        
        # Create the window
        self.window = webview.create_window(
            title='LawGlance - AI Legal Assistant',
            url=f'http://localhost:{STREAMLIT_PORT}',
            js_api=js_api,
            width=1200,
            height=800,
            min_size=(800, 600),
            text_select=True,
            zoomable=True
        )
        
        # Set up handlers for window events
        self.window.events.closed += self.on_closed
    
    def on_closed(self) -> None:
        \"\"\"Handle window close event.\"\"\"
        logger.info("Window closed. Terminating Streamlit...")
        self.terminate()
    
    def terminate(self) -> None:
        \"\"\"Clean up resources and terminate the application.\"\"\"
        if self.streamlit_process and self.streamlit_process.poll() is None:
            logger.info(f"Terminating Streamlit process (PID: {self.streamlit_process.pid})...")
            try:
                # On Windows
                if sys.platform == "win32":
                    self.streamlit_process.terminate()
                # On Unix-like systems
                else:
                    os.killpg(os.getpgid(self.streamlit_process.pid), signal.SIGTERM)
                
                # Give it a moment to terminate gracefully
                try:
                    self.streamlit_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Streamlit did not terminate gracefully, forcing...")
                    self.streamlit_process.kill()
                    
                logger.info("Streamlit process terminated.")
            except Exception as e:
                logger.error(f"Error terminating Streamlit: {e}")
    
    def run(self) -> None:
        \"\"\"Run the desktop application.\"\"\"
        try:
            # Start Streamlit
            self.streamlit_process = self.start_streamlit_server()
            
            # Wait for Streamlit to be ready
            if not self.wait_for_streamlit():
                logger.error("Failed to start Streamlit. Exiting.")
                self.terminate()
                return
            
            # Create and show the window
            self.create_window()
            
            # Register cleanup handler
            atexit.register(self.terminate)
            
            # Start the application
            logger.info("Starting webview application...")
            webview.start(debug=False)
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.terminate()

def main():
    \"\"\"Main entry point for the desktop application.\"\"\"
    print("Starting LawGlance Desktop Application...")
    app = LawGlanceApp()
    app.run()

if __name__ == "__main__":
    main()
""")
    
    # Create a spec file for the PyWebView app
    webview_spec = PROJECT_ROOT / "webview_app.spec"
    
    if not webview_spec.exists():
        logger.info("Creating PyWebView spec file...")
        with open(webview_spec, 'w') as f:
            f.write("""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/desktop/webview_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logo/*.png', 'logo'),
        ('logo/*.ico', 'logo'),
        ('src/ui/*.py', 'src/ui'),
        ('app.py', '.'),
        ('.env', '.'),
        ('requirements.txt', '.')
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.web.bootstrap',
        'langchain',
        'langchain_openai',
        'langchain_chroma'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LawGlance-Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LawGlance-Desktop',
)
""")

    # Add PyWebView to requirements.txt if not already there
    requirements_path = PROJECT_ROOT / "requirements.txt"
    with open(requirements_path, "r") as f:
        requirements = f.read()
    
    if "pywebview" not in requirements:
        logger.info("Adding PyWebView to requirements.txt")
        with open(requirements_path, "a") as f:
            f.write("\n# Desktop app requirements\npywebview>=4.0\n")
    
    # Build the PyWebView app
    try:
        logger.info("Building PyWebView application...")
        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            str(webview_spec)
        ])
        logger.info("✓ PyWebView application build completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ PyWebView application build failed: {e}")
        raise BuildError("PyWebView application build failed")

def clean_build_directories():
    """Clean build directories before new build."""
    logger.info("Cleaning build directories...")
    
    # Directories to clean
    dirs = [
        BUILD_DIR / "LawGlance",
        DIST_DIR / "LawGlance",
    ]
    
    for directory in dirs:
        if directory.exists():
            try:
                shutil.rmtree(directory)
                logger.info(f"✓ Cleaned {directory}")
            except Exception as e:
                logger.warning(f"⚠️ Could not clean {directory}: {e}")

def guid():
    """Generate a simple GUID for the installer."""
    import uuid
    return str(uuid.uuid4()).upper()

def main():
    """Main entry point for the build process."""
    print_banner()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Build LawGlance desktop application")
    
    # Build options
    parser.add_argument("--exe", action="store_true", help="Build executable")
    parser.add_argument("--installer", action="store_true", help="Build installer")
    parser.add_argument("--portable", action="store_true", help="Create portable package")
    parser.add_argument("--webview", action="store_true", help="Create PyWebView application")
    parser.add_argument("--all", action="store_true", help="Build all package types")
    parser.add_argument("--clean", action="store_true", help="Clean build directories before build")
    
    # Executable options
    parser.add_argument("--onefile", action="store_true", help="Create a single executable file")
    parser.add_argument("--console", action="store_true", help="Show console window")
    
    args = parser.parse_args()
    
    # If no build options are specified, prompt the user
    if not (args.exe or args.installer or args.portable or args.webview or args.all):
        print("\nSelect build options:")
        print(" 1. Build executable only")
        print(" 2. Build executable and installer")
        print(" 3. Create portable ZIP package")
        print(" 4. Create PyWebView desktop application")
        print(" 5. Build all")
        print(" 6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ")
            
            if choice == "1":
                args.exe = True
            elif choice == "2":
                args.exe = True
                args.installer = True
            elif choice == "3":
                args.exe = True
                args.portable = True
            elif choice == "4":
                args.webview = True
            elif choice == "5":
                args.all = True
            elif choice == "6":
                print("Exiting...")
                return 0
            else:
                print("Invalid choice. Exiting.")
                return 1
            
        except KeyboardInterrupt:
            print("\nBuild cancelled.")
            return 1
    
    # If --all is specified, set all build options
    if args.all:
        args.exe = True
        args.installer = True
        args.portable = True
        args.webview = True
    
    try:
        # Check environment
        env_info = check_environment()
        
        # Install dependencies
        install_dependencies()
        
        # Clean build directories if requested
        if args.clean:
            clean_build_directories()
        
        # Build executable
        if args.exe:
            build_executable(args)
        
        # Build installer
        if args.installer:
            if not args.exe and not (DIST_DIR / "LawGlance").exists():
                logger.warning("⚠️ Building executable first as it's required for the installer")
                build_executable(args)
            build_installer(args)
        
        # Create portable