@echo off
SETLOCAL EnableDelayedExpansion

echo =================================================
echo             Lawglance System Launcher
echo =================================================
echo.

REM Set Hugging Face token as environment variable
set HUGGINGFACE_API_TOKEN=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
set PYTHONIOENCODING=utf-8

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and try again.
    goto :EXIT
)

REM Look for lawglance_main.py
set FOUND=0
set PROJECT_PATH=%CD%

if exist "%CD%\lawglance_main.py" (
    set FOUND=1
    goto :FOUND_PROJECT
)

if exist "%CD%\OneDrive\Documents\GitHub\lawglance\lawglance_main.py" (
    set FOUND=1
    set PROJECT_PATH=%CD%\OneDrive\Documents\GitHub\lawglance
    goto :FOUND_PROJECT
)

if exist "%USERPROFILE%\OneDrive\Documents\GitHub\lawglance\lawglance_main.py" (
    set FOUND=1
    set PROJECT_PATH=%USERPROFILE%\OneDrive\Documents\GitHub\lawglance
    goto :FOUND_PROJECT
)

:FOUND_PROJECT
if %FOUND% EQU 0 (
    echo Error: Could not find lawglance_main.py
    echo Please navigate to the project directory and try again.
    goto :EXIT
)

echo Found Lawglance at: %PROJECT_PATH%
cd /d "%PROJECT_PATH%"

echo.
echo Choose an option:
echo 1. Run interactive Lawglance system
echo 2. Test document analyzer
echo 3. Test concept extractor
echo 4. Test document editor
echo 5. Test semantic analyzer
echo 6. Install dependencies
echo.

set /p OPTION="Enter your choice (1-6): "

if "%OPTION%"=="1" (
    echo.
    echo Starting Lawglance interactive system...
    echo.
    python -c "import sys; sys.path.append('%PROJECT_PATH%'); from lawglance_runner import run_lawglance; run_lawglance()"
) else if "%OPTION%"=="2" (
    echo.
    echo Testing document analyzer...
    echo.
    python -c "import sys; sys.path.append('%PROJECT_PATH%'); from interactive_test import test_document_analyzer; test_document_analyzer()"
) else if "%OPTION%"=="3" (
    echo.
    echo Testing concept extractor...
    echo.
    python -c "import sys; sys.path.append('%PROJECT_PATH%'); from interactive_test import test_concept_extractor; test_concept_extractor()"
) else if "%OPTION%"=="4" (
    echo.
    echo Testing document editor...
    echo.
    python -c "import sys; sys.path.append('%PROJECT_PATH%'); from interactive_test import test_document_editor; test_document_editor()"
) else if "%OPTION%"=="5" (
    echo.
    echo Testing semantic analyzer...
    echo.
    python -c "import sys; sys.path.append('%PROJECT_PATH%'); from interactive_test import test_semantic_analyzer; test_semantic_analyzer()"
) else if "%OPTION%"=="6" (
    echo.
    echo Installing dependencies...
    echo.
    python -m pip install langchain transformers nltk spacy textstat faiss-cpu python-docx networkx scikit-learn numpy torch huggingface_hub
    python -m spacy download en_core_web_sm
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
    echo.
    echo Dependencies installed. Please restart the script.
) else (
    echo.
    echo Invalid option. Please try again.
)

:EXIT
echo.
pause
