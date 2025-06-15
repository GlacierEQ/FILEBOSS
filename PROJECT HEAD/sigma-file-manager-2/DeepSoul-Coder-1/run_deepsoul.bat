@echo off
echo Starting DeepSoul Code Intelligence System...

REM Run the setup script first time to ensure everything is ready
if not exist deepsoul_config\system_config.json (
    echo First-time setup: Installing dependencies and creating configuration...
    python deepsoul_setup.py
)

REM Check if the user has GPU support
where nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected. Using GPU for inference.
    python deepsoul_launch.py %*
) else (
    echo No NVIDIA GPU detected. Using CPU mode.
    python deepsoul_launch.py --cpu %*
)

pause
