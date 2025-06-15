@echo off
setlocal enabledelayedexpansion

echo =====================================
echo   DeepSeek-Coder Setup Script
echo =====================================

:: Parse arguments
set SKIP_DEPS=0
set EVAL_ONLY=0
set FINETUNE_ONLY=0
set DEMO_ONLY=0
set CREATE_VENV=1
set VENV_NAME=deepsoul-env
set TEST_MODEL=0
set SETUP_CACHE=1

:arg_loop
if "%~1"=="" goto arg_done
if /i "%~1"=="--skip-deps" set SKIP_DEPS=1
if /i "%~1"=="--eval-only" set EVAL_ONLY=1
if /i "%~1"=="--finetune-only" set FINETUNE_ONLY=1
if /i "%~1"=="--demo-only" set DEMO_ONLY=1
if /i "%~1"=="--no-venv" set CREATE_VENV=0
if /i "%~1"=="--venv-name" (
    set VENV_NAME=%~2
    shift
)
if /i "%~1"=="--test-model" set TEST_MODEL=1
if /i "%~1"=="--no-cache" set SETUP_CACHE=0
shift
goto arg_loop
:arg_done

:: Check for Python
echo Checking for Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    exit /b 1
) else (
    echo [32m✓ Python is installed[0m
)

:: Check Python version
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo [31mPython 3.8 or higher is required. Found: %PYTHON_VERSION%[0m
    exit /b 1
) else if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% LSS 8 (
    echo [31mPython 3.8 or higher is required. Found: %PYTHON_VERSION%[0m
    exit /b 1
) else (
    echo [32m✓ Python version %PYTHON_VERSION% is compatible[0m
)

:: Check for pip
echo Checking for pip...
pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [31mError: pip is not installed or not in PATH.[0m
    echo Please install pip and try again.
    exit /b 1
) else (
    echo [32m✓ pip is installed[0m
)

:: Check for git
echo Checking for git...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [33mWarning: git not found. Some features may not work correctly.[0m
) else (
    echo [32m✓ git is installed[0m
)

:: Create virtual environment if requested
if %CREATE_VENV% EQU 1 (
    echo Creating virtual environment '%VENV_NAME%'...
    python -m venv %VENV_NAME%
    
    :: Activate virtual environment
    echo Activating virtual environment...
    call %VENV_NAME%\Scripts\activate.bat
    
    echo [32m✓ Virtual environment created and activated[0m
    echo [33mTo activate the virtual environment in the future, run:[0m
    echo [34m%VENV_NAME%\Scripts\activate.bat[0m
)

:: Install dependencies if not skipped
if %SKIP_DEPS% EQU 0 (
    echo Upgrading pip, setuptools, and wheel...
    pip install --upgrade pip setuptools wheel
    
    if %EVAL_ONLY% EQU 1 (
        echo Installing evaluation dependencies...
        pip install -r Evaluation\HumanEval\requirements.txt
        pip install -r Evaluation\MBPP\requirements.txt
        pip install -r Evaluation\PAL-Math\requirements.txt
        pip install -r Evaluation\DS-1000\requirements.txt
    ) else if %FINETUNE_ONLY% EQU 1 (
        echo Installing fine-tuning dependencies...
        pip install -r finetune\requirements.txt
    ) else if %DEMO_ONLY% EQU 1 (
        echo Installing demo dependencies...
        pip install -r demo\requirements.txt
    ) else (
        echo Installing base dependencies...
        pip install -r requirements.txt
    )
    
    echo [32m✓ Dependencies installed[0m
)

:: Check for CUDA
echo Checking for CUDA support in PyTorch...
python -c "import torch; print('CUDA Available: ' + str(torch.cuda.is_available()))" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [33mWarning: PyTorch not installed or error importing. CUDA status unknown.[0m
) else (
    for /f "tokens=2 delims=:" %%C in ('python -c "import torch; print('CUDA Available: ' + str(torch.cuda.is_available()))"') do (
        set CUDA_STATUS=%%C
        set CUDA_STATUS=!CUDA_STATUS: =!
    )
    
    if "!CUDA_STATUS!"=="True" (
        for /f "tokens=1" %%G in ('python -c "import torch; print(torch.cuda.device_count())"') do set NUM_GPUS=%%G
        echo [32m✓ CUDA is available with !NUM_GPUS! GPU(s)[0m
        python -c "import torch; [print('  {}: {}'.format(i, torch.cuda.get_device_name(i))) for i in range(torch.cuda.device_count())]"
    ) else (
        echo [33mWarning: CUDA is not available. Models will run on CPU which will be very slow.[0m
    )
)

:: Set up model cache
if %SETUP_CACHE% EQU 1 (
    echo Setting up model cache...
    if not exist models mkdir models
    set TRANSFORMERS_CACHE=%CD%\models
    echo [32m✓ Model cache directory created at %CD%\models[0m
    echo [33mTo use this cache location in the future, set:[0m
    echo [34mset TRANSFORMERS_CACHE="%CD%\models"[0m
)

:: Download and test a small model if requested
if %TEST_MODEL% EQU 1 (
    echo Downloading and testing a small model...
    python -c "from transformers import AutoTokenizer; tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/deepseek-coder-1.3b-base', trust_remote_code=True); print('Tokenizer loaded successfully')" 
    if %ERRORLEVEL% EQU 0 (
        echo [32m✓ Test model downloaded successfully[0m
    ) else (
        echo [31m✗ Error downloading test model[0m
    )
)

:: Create data directories
echo Creating necessary directories...
if not exist data mkdir data
if not exist logs mkdir logs

echo [32m=====================================[0m
echo [32m  DeepSeek-Coder setup complete!     [0m
echo [32m=====================================[0m
echo To get started, try the examples in the README.md file.
echo For issues or questions, please visit: https://github.com/deepseek-ai/deepseek-coder
echo.

if %CREATE_VENV% EQU 1 (
    echo [33mRemember to activate the virtual environment with:[0m
    echo [34m%VENV_NAME%\Scripts\activate.bat[0m
)

endlocal
