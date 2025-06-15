@echo off
echo Setting up environment for Unicode support...

:: Set code page to UTF-8
chcp 65001

:: Set Python encoding environment variables
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

:: Echo settings
echo.
echo Environment variables set:
echo PYTHONIOENCODING=%PYTHONIOENCODING%
echo PYTHONLEGACYWINDOWSSTDIO=%PYTHONLEGACYWINDOWSSTDIO%
echo.
echo Code page set to UTF-8 (65001)
echo.
echo You can now run your Python scripts with Unicode support
echo.

:: Keep the window open
pause
