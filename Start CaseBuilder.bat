@echo off
REM Create CaseFiles directory if it doesn't exist
if not exist "%USERPROFILE%\CaseFiles" mkdir "%USERPROFILE%\CaseFiles"

echo Starting CaseBuilder Auto Organizer...
echo.
echo This will automatically organize files from:
echo %USERPROFILE%\CaseFiles
echo.
echo Just drop files into the CaseFiles folder and they'll be
echo automatically processed and organized.
echo.
pause

REM Run the auto organizer
python auto_organize.py

REM If python command fails, try python3
if %ERRORLEVEL% NEQ 0 (
    python3 auto_organize.py
)

pause
