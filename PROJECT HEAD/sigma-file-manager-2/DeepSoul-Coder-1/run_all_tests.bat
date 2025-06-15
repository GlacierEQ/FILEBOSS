@echo off
echo ====================================================
echo   Running All DeepSeek-Coder Tests
echo ====================================================
echo.

REM Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Install pytest if not installed
python -c "import pytest" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing pytest...
    pip install pytest
)

REM Run tests in each directory
echo Running core tests...
python -m pytest tests

echo.
echo Running legal scraping tests...
python -m pytest tests\test_legal_scraping.py

echo.
echo Running demo tests...
python -m pytest demo\tests

echo.
echo Running finetune tests...
python -m pytest finetune\tests

echo.
echo Running evaluation tests...
python -m pytest Evaluation\HumanEval\tests
python -m pytest Evaluation\MBPP\tests
python -m pytest Evaluation\PAL-Math\tests
python -m pytest Evaluation\DS-1000\tests

echo.
echo All tests completed. Check output for any errors.
pause
