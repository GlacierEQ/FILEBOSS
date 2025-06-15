# LawGlance Quick Start Guide

This guide will help you quickly build and run the LawGlance executable with minimal steps.

## Prerequisites

- Windows 10 or 11
- Python 3.8 or later installed
- Internet connection for downloading dependencies

## Building the Executable

### Step 1: Open Command Prompt

Press `Win + R`, type `cmd` and press Enter to open a Command Prompt.

### Step 2: Navigate to LawGlance Directory

Navigate to the LawGlance project directory:
```
cd C:\Users\casey\Desktop\lawglance_project
```

### Step 3: Run the Build Script

Run the build script:
```
python build_desktop_app.py
```

### Step 4: Choose Build Option

You'll see a menu like this:
```
Welcome to the LawGlance Desktop Application Builder!
Please select build options:
1. Build Executable
2. Create Installer
3. Generate Portable Version
```

Type `1` and press Enter to build just the executable.

### Step 5: Wait for Completion

The build process will run for a few minutes. You'll see output like:
```
Building executable...
...
Executable built successfully.
```

### Step 6: Find Your Executable

Navigate to the output folder:
```
cd dist\LawGlance
```

You should find `LawGlance.exe` in this directory.

## Running LawGlance

### Method 1: Direct Execution

Simply double-click on `LawGlance.exe` in the `dist\LawGlance` directory.

### Method 2: Command Line

```
cd C:\Users\casey\Desktop\lawglance_project\dist\LawGlance
LawGlance.exe
```

## Setup for First Use

When you first run LawGlance:

1. Create a file named `.env` in the same folder as the executable
2. Add your OpenAI API key to this file:
   ```
   OPENAI_API_KEY=your_key_here
   ```

## Troubleshooting

### Missing Dependencies

If you see an error about missing dependencies:
```
pip install -r requirements.txt
pip install pyinstaller
```
Then try building again.

### Antivirus Alerts

Some antivirus software may flag the executable. This is a false positive due to how PyInstaller packages Python applications. You can:
1. Add an exception in your antivirus software
2. Use the portable ZIP version instead (option 3 in the build menu)

### "Unable to create process" Error

If you see this error, try running the command prompt as administrator:
1. Right-click on Command Prompt
2. Select "Run as administrator"
3. Navigate to the project directory and try again

### Need More Options?

For more advanced build options, including creating an installer or portable version, see the complete [Build Instructions](BUILD_INSTRUCTIONS.md).
