@echo off
echo ========================================
echo   SIGMA FILEBOSS - Unified File Manager
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
)

REM Check if requirements are installed
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements_sigma.txt
    if errorlevel 1 (
        echo Error: Failed to install requirements
        pause
        exit /b 1
    )
)

echo.
echo Starting SIGMA FILEBOSS...
echo.

REM Launch the application
python launch_sigma_fileboss.py %*

if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)

echo.
echo SIGMA FILEBOSS closed.
pause
