# Visual Guide: Building LawGlance Executable

This step-by-step guide with screenshots will walk you through creating the LawGlance executable file.

## Prerequisites

✅ Windows 10 or 11  
✅ Python 3.8 or later installed  
✅ LawGlance project files  

## Step 1: Open Command Prompt

Press `Win + R` keys, type `cmd`, and press Enter:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │                  Run                         │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Type the name of a program, folder, document,│   │
│  │ or Internet resource, and Windows will open  │   │
│  │ it for you.                                 │   │
│  │                                             │   │
│  │ Open: cmd                                   │   │
│  │                                             │   │
│  │           OK            Cancel              │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Step 2: Navigate to Project Directory

Type the following command and press Enter:

```
cd C:\Users\casey\Desktop\lawglance_project
```

You'll see something like this:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│ C:\WINDOWS\system32>cd C:\Users\casey\Desktop\     │
│ lawglance_project                                  │
│                                                     │
│ C:\Users\casey\Desktop\lawglance_project>          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Step 3: Run the Build Script

Type the following command and press Enter:

```
python build_desktop_app.py
```

You'll see a menu like this:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Welcome to the LawGlance Desktop Application        │
│ Builder!                                            │
│                                                     │
│ Please select build options:                        │
│ 1. Build Executable                                 │
│ 2. Create Installer                                 │
│ 3. Generate Portable Version                        │
│                                                     │
│ Enter your choice (1/2/3):                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Step 4: Select Option 1

Type `1` and press Enter to build just the executable.

## Step 5: Wait for Build to Complete

The build process will run, showing progress like this:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Building executable...                              │
│ 43 INFO: PyInstaller: 5.13.2                        │
│ 43 INFO: Python: 3.9.7                              │
│ 98 INFO: Platform: Windows-10                       │
│ 98 INFO: wrote C:\...\build\LawGlance\LawGlance.spec│
│ 105 INFO: UPX is not available.                     │
│ ...                                                 │
│ 1569 INFO: Copying icons from ['logo/logo.ico']     │
│ ...                                                 │
│ 24170 INFO: Building EXE from out00-EXE.toc         │
│ 24170 INFO: Building EXE from out00-EXE.toc         │
│ 24173 INFO: Appending archive to EXE                │
│ ...                                                 │
│ Executable built successfully.                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

This might take 5-10 minutes depending on your system.

## Step 6: Find Your Executable

Navigate to the dist directory by typing:

```
cd dist\LawGlance
```

You'll see something like:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│ C:\Users\casey\Desktop\lawglance_project>cd dist\  │
│ LawGlance                                           │
│                                                     │
│ C:\Users\casey\Desktop\lawglance_project\dist\     │
│ LawGlance>dir                                       │
│                                                     │
│ Directory of C:\Users\casey\Desktop\lawglance_      │
│ project\dist\LawGlance                              │
│                                                     │
│ 05/15/2023  02:45 PM    <DIR>          .            │
│ 05/15/2023  02:45 PM    <DIR>          ..           │
│ 05/15/2023  02:45 PM        14,628,864 LawGlance.exe│
│ ...                                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Step 7: Create a .env File

Create a file named `.env` in the same folder as the executable to store your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Step 8: Run the Executable

Double-click on `LawGlance.exe` or type:

```
LawGlance.exe
```

The application will start and open in your browser:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│ Starting LawGlance...                               │
│ Information: Running on http://localhost:8501       │
│ You can now view your Streamlit app in your browser.│
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Troubleshooting Common Issues

### Icon Not Found
```
File "logo/logo.ico" not found
```

**Solution**: Run this command to create a logo:
```
python -c "from logo.create_placeholder_logo import create_placeholder_logo; create_placeholder_logo()"
```

### Missing Module
```
ImportError: No module named 'streamlit'
```

**Solution**: Install all requirements:
```
pip install -r requirements.txt
pip install pyinstaller
```

### Antivirus Blocking
If your antivirus blocks the executable:

1. Add an exception in your antivirus software
2. Use option 3 (portable version) instead

### Still Having Problems?

For more detailed help, follow the full [BUILD_INSTRUCTIONS.md](../BUILD_INSTRUCTIONS.md) guide.

## Success! 🎉

You now have a standalone executable file that can be run on any Windows system without requiring Python to be installed.
