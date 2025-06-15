@echo off
title Sorting Hat Permission Fix
cd /d "%~dp0"
echo ===================================================
echo     SORTING HAT PERMISSION FIX UTILITY
echo ===================================================

echo This utility will help resolve permission issues with the Sorting Hat.
echo.
echo The following actions will be performed:
echo 1. Grant proper permissions to access Documents folder
echo 2. Create necessary folders with correct access rights
echo 3. Restart the file organizer with elevated permissions
echo.

echo Checking for administrative rights...
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrative privileges.
) else (
    echo This script requires administrative privileges.
    echo Please right-click and select "Run as administrator".
    pause
    exit /b 1
)

echo.
echo Setting permissions for Documents folder...
icacls "C:\Users\casey\Documents" /grant "casey:(OI)(CI)F" /T /C /Q

echo.
echo Creating and checking destination folders...
if not exist "C:\Users\casey\OrganizeFolder" mkdir "C:\Users\casey\OrganizeFolder"

echo Granting permissions to destination folders...
icacls "C:\Users\casey\OrganizeFolder" /grant "casey:(OI)(CI)F" /T /C /Q

echo.
echo Restarting file organizer service...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq Sorting Hat - File Monitor*" >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting file organizer with elevated permissions...
start "Sorting Hat - File Monitor" cmd /c "node file_organizer.js"

echo.
echo ===================================================
echo Permission fix complete! The file organizer should now
echo work properly without permission errors.
echo ===================================================
pause
