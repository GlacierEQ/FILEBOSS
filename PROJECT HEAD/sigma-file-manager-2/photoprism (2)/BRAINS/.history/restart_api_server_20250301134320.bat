@echo off
title Restart Sorting Hat API Server
cd /d "%~dp0"

echo ===================================================
echo          SORTING HAT API SERVER RESTART
echo ===================================================
echo.

echo Step 1: Stopping any running Node.js processes...
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo Step 2: Clearing any port conflicts...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
  taskkill /F /PID %%a >nul 2>&1
)

echo Step 3: Creating required directories...
if not exist "cache" mkdir cache
if not exist "public" mkdir public

echo Step 4: Starting API server...
start "Sorting Hat API Server" cmd /c "node service.js"

echo.
echo ===================================================
echo API Server restarted! The dashboard is available at:
echo http://localhost:3000/
echo ===================================================

pause
