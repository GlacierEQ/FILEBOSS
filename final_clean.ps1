# Final Cleanup Script - Aggressive Startup Item Removal
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== FINAL CLEANUP - AGGRESSIVE MODE ===" -ForegroundColor Red -BackgroundColor White
Write-Host "This script will aggressively remove all non-essential startup items."
Write-Host "Only critical system items will be preserved.\n"

# List of items to target for removal
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

# 1. Disable from Task Scheduler
Write-Host "`n[1/4] Disabling from Task Scheduler..." -ForegroundColor Yellow
$tasks = Get-ScheduledTask | Where-Object { $_.State -ne "Disabled" }

foreach ($task in $tasks) {
    $taskName = $task.TaskName
    $shouldRemove = $false
    
    foreach ($target in $targetItems) {
        if ($taskName -like "*$target*") {
            $shouldRemove = $true
            break
        }
    }
    
    if ($shouldRemove) {
        try {
            $task | Disable-ScheduledTask -ErrorAction Stop
            Write-Host "  - Disabled task: $taskName" -ForegroundColor Green
        } catch {
            Write-Host "  ! Could not disable task '$taskName': $_" -ForegroundColor Red
        }
    }
}

# 2. Remove from Registry
Write-Host "`n[2/4] Removing from Registry..." -ForegroundColor Yellow
$regPaths = @(
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
)

foreach ($path in $regPaths) {
    if (Test-Path $path) {
        $regKey = Get-Item -Path $path -ErrorAction SilentlyContinue
        if ($regKey) {
            $values = $regKey.GetValueNames()
            foreach ($value in $values) {
                $shouldRemove = $false
                foreach ($target in $targetItems) {
                    if ($value -like "*$target*") {
                        $shouldRemove = $true
                        break
                    }
                }
                
                if ($shouldRemove) {
                    try {
                        Remove-ItemProperty -Path $path -Name $value -Force -ErrorAction Stop
                        Write-Host "  - Removed from $path: $value" -ForegroundColor Green
                    } catch {
                        Write-Host "  ! Could not remove '$value' from $path: $_" -ForegroundColor Red
                    }
                }
            }
        }
    }
}

# 3. Clean Startup Folders
Write-Host "`n[3/4] Cleaning Startup Folders..." -ForegroundColor Yellow
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
            $itemName = $item.Name
            $shouldRemove = $false
            
            foreach ($target in $targetItems) {
                if ($itemName -like "*$target*") {
                    $shouldRemove = $true
                    break
                }
            }
            
            if ($shouldRemove) {
                try {
                    Remove-Item -Path $item.FullName -Force -Recurse -ErrorAction Stop
                    Write-Host "  - Removed from $folder: $itemName" -ForegroundColor Green
                } catch {
                    Write-Host "  ! Could not remove '$itemName' from $folder: $_" -ForegroundColor Red
                }
            }
        }
    }
}

# 4. Disable Services
Write-Host "`n[4/4] Disabling Non-Essential Services..." -ForegroundColor Yellow
$services = Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' }

foreach ($service in $services) {
    $serviceName = $service.DisplayName
    $shouldDisable = $false
    
    foreach ($target in $targetItems) {
        if ($serviceName -like "*$target*") {
            $shouldDisable = $true
            break
        }
    }
    
    if ($shouldDisable) {
        try {
            Set-Service -Name $service.Name -StartupType Manual -ErrorAction Stop
            Write-Host "  - Set to manual: $serviceName" -ForegroundColor Green
        } catch {
            Write-Host "  ! Could not configure service '$serviceName': $_" -ForegroundColor Red
        }
    }
}

# Final Instructions
Write-Host "`n=== FINAL CLEANUP COMPLETE ===" -ForegroundColor Cyan
Write-Host "1. A SYSTEM RESTART IS REQUIRED to ensure all changes take effect."
Write-Host "2. After restart, check if the black screen issue is resolved."
Write-Host "3. If issues persist, we may need to perform additional troubleshooting."
Write-Host "   - Check Event Viewer for system errors"
Write-Host "   - Run system file checker (sfc /scannow)"
Write-Host "   - Consider a clean boot for further diagnosis"

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
