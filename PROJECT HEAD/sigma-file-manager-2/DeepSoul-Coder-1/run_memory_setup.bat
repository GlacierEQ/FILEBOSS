@echo off
echo ====================================================
echo    DeepSeek-Coder Memory Protection Setup
echo ====================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [31mERROR: Python is not installed or not in PATH[0m
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Install required packages for memory management
echo Installing memory management dependencies...
pip install psutil nvidia-ml-py3 py3nvml torch

REM Create memory dumps directory
echo Creating memory dumps directory...
mkdir memory_dumps 2>nul

REM Run the memory protection setup script
echo.
echo [32mSetting up memory protection system...[0m
echo.
python utils\setup_memory_protection.py

echo.
if %errorlevel% equ 0 (
    echo [32m==============================================[0m
    echo [32m  Memory protection system setup complete!   [0m
    echo [32m==============================================[0m
    echo.
    echo Memory protection is now active for all DeepSoul operations.
) else (
    echo [31m==============================================[0m
    echo [31m  ERROR: Memory protection setup failed      [0m
    echo [31m==============================================[0m
)

pause
