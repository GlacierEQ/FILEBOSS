# LawGlance Quick Build Guide

This is a simplified guide for building LawGlance into an executable application.

## Quick Start (Windows)

### One-Click Build

The easiest way to build LawGlance is using the included batch file:

1. Double-click `build.bat` in the project folder
2. Select option 2 for a complete installer
3. Wait for the build to complete
4. Find your installer at `build/installer/LawGlance-Setup.exe`

That's it! You now have a ready-to-install LawGlance application.

## Alternative Quick Methods

### Using the build script directly

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run the build script
python scripts/build.py --all
```

### One-line PyInstaller command

If you just want a simple executable quickly:

```bash
pip install pyinstaller && pyinstaller --onefile --windowed --icon=logo/logo.ico app.py
```

## Need More Details?

For complete build instructions, troubleshooting, and advanced options, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)
