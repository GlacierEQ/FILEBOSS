# Building LawGlance Executable: Simple Guide

This guide provides the simplest steps to build the LawGlance executable file with minimal fuss.

## Requirements

- Windows 10/11
- Python 3.8 or newer
- Administrator access (recommended)

## Step-by-Step Instructions

### 1. Open Command Prompt

- Press `Win + R`
- Type `cmd` and press Enter

### 2. Navigate to Project Folder

```bash
cd C:\Users\casey\Desktop\lawglance_project
```

### 3. Run the Build Script

```bash
python build_desktop_app.py
```

### 4. Select Build Option

When prompted, type `1` and press Enter to build the executable only.

### 5. Wait for Completion

The build process will run for a few minutes. You'll see progress messages.

### 6. Find Your Executable

When finished, your executable will be at:
```
C:\Users\casey\Desktop\lawglance_project\dist\LawGlance\LawGlance.exe
```

### 7. Test Your Executable

Double-click `LawGlance.exe` to run it.

## Common Issues & Solutions

### "Module not found" errors

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Antivirus blocks the build process

Temporarily disable your antivirus or add an exception for PyInstaller.

### "Permission denied" errors

Run Command Prompt as Administrator:
1. Search for "Command Prompt"
2. Right-click and select "Run as administrator"
3. Then follow steps 2-7 above

### Build seems to hang

The process may take several minutes depending on your system. Be patient.

### Executable fails to start

Make sure you have a `.env` file with your API key in the same folder as the executable.

## Next Steps

- For a complete installer: Run the script again and choose option 2
- For a portable version: Run the script again and choose option 3
- For more detailed instructions, see [QUICK_START.md](QUICK_START.md)
