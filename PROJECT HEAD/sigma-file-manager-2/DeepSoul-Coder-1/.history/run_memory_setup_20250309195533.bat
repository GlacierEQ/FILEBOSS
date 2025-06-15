@echo off
echo ====================================================
echo   MemoryPlugin MCP Server Setup for Claude Desktop
echo ====================================================
echo.
echo This will configure Claude Desktop to use MemoryPlugin.
echo.

REM Run the setup script
python claude_memory_setup.py %*

pause
