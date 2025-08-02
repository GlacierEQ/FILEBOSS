# Direct Registry Cleanup Script
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== DIRECT REGISTRY CLEANUP ===" -ForegroundColor Red -BackgroundColor White
Write-Host "This script will directly modify the registry to remove persistent startup items.\n"

# 1. Define registry keys to clean
$registryPaths = @(
    # User-specific startup
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
    
    # System-wide startup
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
)

# 2. Items to target for removal
$targetItems = @(
    # Google Drive items
    "GoogleDriveFS",
    "Google Drive",
    
    # Razer items
    "Razer",
    "RazerAxon",
    "RazerAppEngine",
    "RazerCortex",
    "Razer Synapse",
    
    # Other identified items
    "4-Organizer",
    "ChatGPT",
    "EPPCCMON",
    "Stickies",
    "mymap",
    "Ollama",
    "podman",
    "Perfect Memory",
    "Intel Processor Identification"
)

# 3. Function to remove matching registry values
function Remove-MatchingRegistryValues {
    param (
        [string]$path,
        [string[]]$patterns
    )
    
    if (-not (Test-Path $path)) {
        Write-Host "  - Path not found: $path" -ForegroundColor Yellow
        return
    }
    
    $key = Get-Item -Path $path
    $values = $key.GetValueNames()
    $removed = $false
    
    foreach ($value in $values) {
        foreach ($pattern in $patterns) {
            if ($value -like "*$pattern*") {
                try {
                    Remove-ItemProperty -Path $path -Name $value -Force -ErrorAction Stop
                    Write-Host "  - Removed: $value from $path" -ForegroundColor Green
                    $removed = $true
                    break
                } catch {
                    Write-Host "  ! Failed to remove $value from $path : $_" -ForegroundColor Red
                }
            }
        }
    }
    
    if (-not $removed) {
        Write-Host "  - No matching items found in $path" -ForegroundColor Gray
    }
}

# 4. Process each registry path
Write-Host "`n[1/3] Cleaning registry startup items..." -ForegroundColor Yellow
foreach ($path in $registryPaths) {
    Write-Host "`nChecking: $path" -ForegroundColor Cyan
    Remove-MatchingRegistryValues -path $path -patterns $targetItems
}

# 5. Check and clean scheduled tasks
Write-Host "`n[2/3] Checking scheduled tasks..." -ForegroundColor Yellow
foreach ($item in $targetItems) {
    $tasks = Get-ScheduledTask | Where-Object { $_.TaskName -like "*$item*" -and $_.State -ne "Disabled" }
    foreach ($task in $tasks) {
        try {
            $task | Disable-ScheduledTask -ErrorAction Stop | Out-Null
            Write-Host "  - Disabled task: $($task.TaskName)" -ForegroundColor Green
        } catch {
            Write-Host "  ! Could not disable task '$($task.TaskName)': $_" -ForegroundColor Red
        }
    }
}

# 6. Clean startup folders
Write-Host "`n[3/3] Cleaning startup folders..." -ForegroundColor Yellow
$startupFolders = @(
    [Environment]::GetFolderPath('Startup'),
    [Environment]::GetFolderPath('CommonStartup'),
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
)

foreach ($folder in $startupFolders) {
    if (Test-Path $folder) {
        $items = Get-ChildItem -Path $folder -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            foreach ($target in $targetItems) {
                if ($item.Name -like "*$target*") {
                    try {
                        Remove-Item -Path $item.FullName -Force -Recurse -ErrorAction Stop
                        Write-Host "  - Removed from $folder: $($item.Name)" -ForegroundColor Green
                    } catch {
                        Write-Host "  ! Could not remove '$($item.Name)' from $folder: $_" -ForegroundColor Red
                    }
                    break
                }
            }
        }
    }
}

# 7. Final instructions
Write-Host "`n=== REGISTRY CLEANUP COMPLETE ===" -ForegroundColor Cyan
Write-Host "1. A SYSTEM RESTART IS REQUIRED for all changes to take effect."
Write-Host "2. After restart, check if the black screen issue is resolved."
Write-Host "3. If issues persist, we may need to:"
Write-Host "   - Run System File Checker (sfc /scannow)"
Write-Host "   - Perform a clean boot"
Write-Host "   - Check for problematic drivers"

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
