@echo off
title Sorting Hat Watchdog
cd /d "%~dp0"
echo ===================================================
echo         SORTING HAT WATCHDOG SERVICE
echo ===================================================
echo.

echo Starting Sorting Hat Watchdog (System Protection Service)...
echo This service will monitor and automatically restart other
echo Sorting Hat components if they crash or use too much memory.
echo.

echo Starting watchdog with system protection...
node watchdog.js

echo.
echo Watchdog stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
start "" "%~f0"
