@echo off
echo Starting DeepSoul Code Intelligence System...

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
