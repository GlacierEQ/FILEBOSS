@echo off
title Sorting Hat System Startup
cd /d "%~dp0"
echo ===================================================
echo          SORTING HAT SYSTEM INITIALIZATION
echo ===================================================
echo.

:: Check if Node.js is installed
echo Checking for Node.js...
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Node.js is not installed. Please install Node.js to continue.
  echo Visit https://nodejs.org/ to download.
  pause
  exit /b 1
) else (
  echo Node.js found: 
  node --version
)

:: Install dependencies
echo.
echo Installing dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Failed to install dependencies.
  pause
  exit /b 1
) else (
  echo Dependencies installed successfully.
)

:: Create necessary folders
echo.
echo Setting up folders...
call setup_folders.bat
if %ERRORLEVEL% NEQ 0 (
  echo WARNING: Folder setup may not have completed successfully.
) else (
  echo Folders set up successfully.
)

:: Run troubleshooter to ensure network connectivity
echo.
echo Running network diagnostics...
node troubleshoot.js
echo Network setup complete.

:: Start services
echo.
echo Starting services...
echo.
echo 1. Starting file monitoring service...
start "Sorting Hat - File Monitor" cmd /c "node file_organizer.js"

echo 2. Starting API service...
start "Sorting Hat - API Service" cmd /c "node service.js"

:: Create a test file to verify sorting is working
echo.
echo Creating test files to verify sorting functionality...
echo This is a test legal document > "C:\Users\casey\Documents\test_legal_document.txt"
echo This is a test financial statement > "C:\Users\casey\Documents\test_financial_statement.txt"

echo.
echo ===================================================
echo          SORTING HAT SYSTEM IS NOW ACTIVE
echo ===================================================
echo.
echo The Sorting Hat system is now monitoring your Documents folder.
echo Files will be automatically sorted into categories in:
echo C:\Users\casey\OrganizeFolder
echo.
echo Services running:
echo  - File Organizer (watching for new files)
echo  - API Service (running on http://localhost:3000)
echo.
echo To add Sorting Hat to Windows startup, run:
echo  python add_to_startup.py
echo.
echo To stop all services, press Ctrl+C in each service window
echo or run taskkill /F /IM node.exe /T
echo ===================================================

pause
