# LawGlance: Building the Executable

This guide provides step-by-step instructions to build LawGlance into a downloadable, self-contained executable application.

## Prerequisites

- Python 3.8 or later
- Git (for cloning the repository)
- Windows OS (for installer creation)

## Method 1: Using the Build Script (Recommended)

LawGlance includes a build script that automates the process of creating executables, installers, and portable versions.

### Step 1: Prepare your environment

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install required packages
pip install -r requirements.txt
```

### Step 2: Run the build script

```bash
python build_desktop_app.py
```

### Step 3: Select your build option

The script will present several options:
1. Build executable only
2. Build executable and installer
3. Create portable ZIP package
4. Create PyWebView desktop application
5. Build all

Choose option 2 or 5 for a full installation package.

### Step 4: Locate your builds

After the build process completes:
- Executable: `dist/LawGlance/LawGlance.exe`
- Installer: `build/installer/LawGlance-Setup.exe`
- Portable ZIP: `output/LawGlance-Portable.zip`

## Method 2: Manual PyInstaller Commands

If you prefer more control over the build process, you can use PyInstaller directly.

### Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

### Step 2: Build using the spec file

```bash
pyinstaller lawglance.spec
```

### Step 3: Build the installer (optional)

If you have Inno Setup installed:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

## Method 3: Simple One-File Executable

For a quick, simple executable without the full installer:

```bash
pyinstaller --onefile --windowed --icon=logo/logo.ico app.py --name LawGlance
```

## Troubleshooting

### Missing dependencies

If you encounter missing dependency errors:

```bash
pip install pyinstaller pillow
```

### Hidden imports

If certain modules aren't being included:

```bash
pyinstaller --onefile --windowed --hidden-import=streamlit.web.bootstrap --hidden-import=langchain_openai app.py
```

### Icon issues

Make sure the logo exists:

```bash
python -c "from logo.create_placeholder_logo import create_placeholder_logo; create_placeholder_logo()"
```

## Distribution

After building, you can distribute LawGlance in several ways:

1. **Full Installer**: Share the `LawGlance-Setup.exe` file for a standard installation experience
2. **Portable Version**: Share the ZIP file for users who prefer not to install software
3. **Standalone EXE**: Share just the EXE file for simple execution

## Additional Notes

- The application requires an internet connection for API access
- First-time users will need to provide their own API keys in the `.env` file
- The executable may be flagged by some antivirus software due to the packaging method
