@echo off
REM DeepSeek-Coder Setup Script for Windows
REM This script helps set up the environment for DeepSeek-Coder

setlocal enabledelayedexpansion

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"

echo.
echo ===========================
echo   DeepSeek-Coder Setup
echo ===========================
echo.

REM Check for Python
echo Checking Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not found in PATH. Please install Python 3.8 or higher.
    goto :error
)

REM Check Python version
for /f "tokens=2" %%i in ('python -c "import sys; print(sys.version.split()[0])"') do set python_version=%%i
echo Python version: %python_version%

REM Parse version number and check if it's at least 3.8
for /f "tokens=1,2 delims=." %%a in ("%python_version%") do (
    set "major=%%a"
    set "minor=%%b"
)

if %major% LSS 3 (
    echo ERROR: Python version is too old. DeepSeek-Coder requires Python 3.8 or higher.
    goto :error
) else if %major% EQU 3 (
    if %minor% LSS 8 (
        echo ERROR: Python version is too old. DeepSeek-Coder requires Python 3.8 or higher.
        goto :error
    )
)

REM Check for pip
echo Checking pip installation...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: pip is not installed or not in PATH.
    echo Attempting to install pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install pip. Please install pip manually.
        goto :error
    )
)

REM Check for CUDA support
echo Checking for NVIDIA GPU...
where nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected.
    echo Running NVIDIA diagnostics...
    nvidia-smi
) else (
    echo No NVIDIA GPU detected. CPU mode will be used.
    echo For optimal performance, an NVIDIA GPU with CUDA support is recommended.
)

REM Check for virtual environment
if exist "%SCRIPT_DIR%venv" (
    echo Virtual environment found. Activating...
    if exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
        call "%SCRIPT_DIR%venv\Scripts\activate.bat"
        echo Virtual environment activated.
    ) else (
        echo WARNING: Found venv directory but couldn't locate activation script.
    )
) else (
    echo No virtual environment found at %SCRIPT_DIR%venv
    echo You can create one using: python -m venv venv
    echo Continuing with system Python...
)

REM Check for git
echo Checking for Git...
where git >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('git --version') do set git_version=%%i
    echo %git_version% detected.
    
    REM Check for Git LFS
    git lfs version >nul 2>&1
    if %errorlevel% equ 0 (
        echo Git LFS is installed.
    ) else (
        echo WARNING: Git LFS is not installed.
        echo Git LFS is recommended for downloading large model files.
        echo Install from: https://git-lfs.github.com/
    )
) else (
    echo WARNING: Git is not installed. Some dataset downloads may not work properly.
    echo Install from: https://git-scm.com/download/win
)

REM Run the setup.py script
echo.
echo ===========================
echo   Running Setup Script
echo ===========================
echo.

python "%SCRIPT_DIR%setup.py" %*
set SETUP_EXIT_CODE=%errorlevel%

if %SETUP_EXIT_CODE% neq 0 (
    echo.
    echo Setup encountered errors. Please check the output above for details.
    goto :error
) else (
    echo.
    echo Setup completed successfully!
)

echo.
echo ===========================
echo   Additional Information
echo ===========================
echo.
echo If you encountered any issues, please check the following:
echo 1. Make sure you have Python 3.8 or higher installed.
echo 2. If you're using a virtual environment, ensure it's activated.
echo 3. For GPU support, make sure you have NVIDIA drivers installed and compatible with CUDA 11.8.
echo 4. Check the README.md for more information on usage and requirements.
echo.
echo For more help, visit: https://github.com/deepseek-ai/deepseek-coder/issues
echo.
pause
exit /b 0

:error
echo.
echo Setup failed! Please fix the issues above and try again.
pause
exit /b 1
