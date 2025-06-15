@echo off
echo ====================================================
echo    Building DeepSoul AION-777 Autonomous System
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

REM First run setup if needed
if not exist deepsoul_config\system_config.json (
    echo First-time setup: Installing dependencies and creating configuration...
    python deepsoul_setup.py
    if %errorlevel% neq 0 (
        echo [31mSetup failed. Please check the error messages above.[0m
        pause
        exit /b 1
    )
)

REM Create necessary directories
echo Creating AION-777 directories...
mkdir aion777_training 2>nul
mkdir aion777_checkpoints 2>nul
mkdir aion777_models 2>nul

REM Run the AION-777 training process
echo.
echo [32mInitializing AION-777 training process...[0m
echo.
python aion777_trainer.py

echo.
if %errorlevel% equ 0 (
    echo [32m====================================================[0m
    echo [32m  DeepSoul AION-777 training process complete!     [0m
    echo [32m====================================================[0m
    echo.
    echo Launch the system with: python deepsoul_launch.py --aion777
) else (
    echo [31m====================================================[0m
    echo [31m  ERROR: Training process encountered problems      [0m
    echo [31m====================================================[0m
)

pause
