@echo off
echo Starting Natural Language Organizer...
echo.

REM Check if Python is in path
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found in PATH. Please install Python or add it to your PATH.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Launch the natural language organizer GUI
cd /d "%~dp0"
python nl_gui.py

REM If Python returns an error
if %errorlevel% neq 0 (
    echo Error launching Natural Language Organizer.
    echo.
    echo Try running install_dependencies.py first:
    echo python install_dependencies.py
    echo.
    echo Press any key to exit...
    pause >nul
)
