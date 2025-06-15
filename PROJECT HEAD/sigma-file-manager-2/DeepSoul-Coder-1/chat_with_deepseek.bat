@echo off
echo Starting DeepSeek-Coder Chat Interface...

REM Check if the user has GPU support
where nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected. Using GPU for inference.
    python talk_with_deepseek.py %*
) else (
    echo No NVIDIA GPU detected. Using CPU mode with 1.3B model.
    python talk_with_deepseek.py --cpu --model deepseek-ai/deepseek-coder-1.3b-instruct %*
)

pause
