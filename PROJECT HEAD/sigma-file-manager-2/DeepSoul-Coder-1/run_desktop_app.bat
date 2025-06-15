@echo off
echo ====================================================
echo   DeepSeek-Coder Desktop Application
echo ====================================================
echo.

setlocal

REM Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check for required packages
python -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyQt6...
    pip install PyQt6
)

REM Check for model dependencies
python -c "import transformers" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing transformers...
    pip install transformers
)

REM Create directories if needed
if not exist "memory_dumps" mkdir memory_dumps
if not exist "deepsoul_config" mkdir deepsoul_config

REM Run the desktop application
echo Starting DeepSeek-Coder desktop application...
echo.
python gui\desktop_app.py %*

REM Check for errors
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application exited with code %errorlevel%
    echo.
    echo If you're experiencing issues, please check the logs in deepsoul_gui.log
)

echo.
pause
