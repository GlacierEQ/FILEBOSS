@echo off
echo ====================================================
echo   Setting up MemoryPlugin for Claude Desktop
echo ====================================================
echo.
echo Using API Token: LFvblPuL3N8N8k2FLyGcsCkMSMSrHsG9
echo.

REM Run the setup script with your API token
python claude_memory_setup.py --token LFvblPuL3N8N8k2FLyGcsCkMSMSrHsG9

echo.
echo If setup was successful, Claude Desktop now has access to your MemoryPlugin account.
echo You can use the following tools in Claude:
echo  - store_memory: Store new memories
echo  - get_memories: Query your memories
echo  - list_buckets: View all memory buckets
echo  - create_bucket: Create new memory buckets
echo  - get_memories_and_buckets: Combined query for efficiency
echo.
pause
