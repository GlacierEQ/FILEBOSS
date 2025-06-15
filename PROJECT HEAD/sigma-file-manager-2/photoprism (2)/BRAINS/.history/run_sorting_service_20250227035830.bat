@echo off
title Sorting Hat Service
cd /d "%~dp0"
echo Starting Sorting Hat Service...
echo Timestamp: %date% %time%

:: Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Node.js is not installed. Please install Node.js to run this service.
  pause
  exit /b 1
)

:: Start the service
echo Starting service...
node service.js

:: If the service exits, restart it (unless it's a clean exit)
if %ERRORLEVEL% NEQ 0 (
  echo Service crashed with error code %ERRORLEVEL%
  echo Restarting in 5 seconds...
  timeout /t 5
  start "" "%~f0"
)

exit /b 0
