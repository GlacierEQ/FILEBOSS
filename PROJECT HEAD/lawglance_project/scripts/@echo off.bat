@echo off
:: One-click build script for LawGlance
:: Just double-click this file to build the executable

echo ==========================================================
echo               LAWGLANCE EXECUTABLE BUILDER
echo ==========================================================
echo.
echo This script will walk you through building LawGlance.
echo.
echo Before we begin, we'll check your environment...
echo.

:: Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or newer and try again.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYVER=%%I
echo Found Python %PYVER%

:: Check for pip
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip is not installed or not working.
    echo Please fix your Python installation and try again.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo Installing required packages...
python -m pip install --upgrade pyinstaller pillow
python -m pip install -r requirements.txt

echo.
echo Creating the LawGlance executable...
echo This may take several minutes. Please be patient.
echo.

:: Create a logo if it doesn't exist
if not exist logo\logo.ico (
    echo Creating logo...
    mkdir logo 2>nul
    python -c "import os; os.makedirs('logo', exist_ok=True); from PIL import Image, ImageDraw; img = Image.new('RGB', (256, 256), color=(33, 150, 243)); draw = ImageDraw.Draw(img); draw.rectangle([64, 170, 192, 192], fill=(255, 255, 255)); draw.rectangle([118, 64, 138, 170], fill=(255, 255, 255)); draw.ellipse([64, 64, 114, 114], outline=(255, 255, 255), width=10); draw.ellipse([162, 64, 212, 114], outline=(255, 255, 255), width=10); img.save('logo/logo.png'); img.save('logo/logo.ico', sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])"
)

:: Build the executable
python -m PyInstaller --name=LawGlance --onefile --windowed --icon=logo/logo.ico --add-data "logo;logo" app.py

echo.
if %ERRORLEVEL% == 0 (
    echo ==========================================================
    echo               BUILD SUCCESSFUL!
    echo ==========================================================
    echo.
    echo Your LawGlance executable is ready at:
    echo dist\LawGlance.exe
    echo.
    echo NEXT STEPS:
    echo 1. Create a .env file in the same directory as the executable
    echo 2. Add your OpenAI API key to the .env file:
    echo    OPENAI_API_KEY=your_api_key_here
    echo 3. Run LawGlance.exe to start the application
) else (
    echo ERROR: Build failed! Please check the error messages above.
)

echo.
echo Press any key to exit...
pause >nul