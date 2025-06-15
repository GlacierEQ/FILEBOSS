@echo off
title Sorting Hat Troubleshooter
cd /d "%~dp0"
echo Running Sorting Hat Troubleshooter...
echo Timestamp: %date% %time%

:: Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Node.js is not installed. Please install Node.js to run this tool.
  pause
  exit /b 1
)

:: Run the troubleshooting script
echo Starting troubleshooting...
node troubleshoot.js

echo.
echo Troubleshooting completed.
echo.

:: Restart the service
echo Restarting the Sorting Hat service...
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
start "" "%~dp0run_sorting_service.bat"

echo Service restarted. Please check the dashboard again.
pause
