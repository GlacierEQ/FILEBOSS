# ULTIMATE CLEANUP SCRIPT
# WARNING: This script performs aggressive cleanup of startup items
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== ULTIMATE STARTUP CLEANER ===" -ForegroundColor White -BackgroundColor Red
Write-Host "WARNING: This script will aggressively clean all non-essential startup items"
Write-Host "Only critical system items will be preserved.\n"

# 1. First, create a system restore point
try {
    Write-Host "Creating system restore point..." -ForegroundColor Cyan
    Checkpoint-Computer -Description "Before Ultimate Clean Script" -RestorePointType MODIFY_SETTINGS
    Write-Host "  - System restore point created successfully" -ForegroundColor Green
} catch {
    Write-Host "  ! Could not create system restore point: $_" -ForegroundColor Red
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y") { exit }
}

# 2. List of items to KEEP (system critical)
$safeItems = @(
    "Windows Defender",
    "SecurityHealth",
    "RtkAudUService",
    "NvBackend",
    "NvNode",
    "NVIDIA",
    "Intel",
    "Realtek",
    "Synaptics",
    "Microsoft"
)

# 3. Function to check if an item is safe to keep
function Is-SafeItem($itemName) {
    if ([string]::IsNullOrEmpty($itemName)) { return $false }
    
    $itemName = $itemName.ToLower()
    foreach ($safe in $safeItems) {
        if ($itemName.Contains($safe.ToLower())) {
            return $true
        }
    }
    return $false
}

# 4. Clean Task Scheduler
Write-Host "`n[1/4] Cleaning Task Scheduler..." -ForegroundColor Yellow
$tasks = Get-ScheduledTask | Where-Object { $_.State -ne "Disabled" }

foreach ($task in $tasks) {
    $taskName = $task.TaskName
    
    if (Is-SafeItem $taskName) {
        Write-Host "  - Keeping (safe): $taskName" -ForegroundColor Cyan
        continue
    }
    
    # Skip Microsoft and Windows tasks
    if ($task.TaskPath -like "\Microsoft\*" -or $task.TaskPath -like "\Windows\*") {
        Write-Host "  - Keeping (system): $taskName" -ForegroundColor Cyan
        continue
    }
    
    try {
        $task | Disable-ScheduledTask -ErrorAction Stop | Out-Null
        Write-Host "  - Disabled: $taskName" -ForegroundColor Green
    } catch {
        Write-Host "  ! Could not disable task '$taskName': $_" -ForegroundColor Red
    }
}

# 5. Clean Registry
Write-Host "`n[2/4] Cleaning Registry..." -ForegroundColor Yellow
$regPaths = @(
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
)

foreach ($path in $regPaths) {
    if (-not (Test-Path $path)) { continue }
    
    Write-Host "`nChecking: $path" -ForegroundColor Cyan
    $regKey = Get-Item -Path $path -ErrorAction SilentlyContinue
    if (-not $regKey) { continue }
    
    $values = $regKey.GetValueNames()
    $removed = $false
    
    foreach ($value in $values) {
        if (Is-SafeItem $value) {
            Write-Host "  - Keeping (safe): $value" -ForegroundColor Cyan
            continue
        }
        
        try {
            Remove-ItemProperty -Path $path -Name $value -Force -ErrorAction Stop
            Write-Host "  - Removed: $value" -ForegroundColor Green
            $removed = $true
        } catch {
            Write-Host "  ! Could not remove '$value': $_" -ForegroundColor Red
        }
    }
    
    if (-not $removed) {
        Write-Host "  - No non-essential items found" -ForegroundColor Gray
    }
}

# 6. Clean Startup Folders
Write-Host "`n[3/4] Cleaning Startup Folders..." -ForegroundColor Yellow
$startupFolders = @(
    [Environment]::GetFolderPath('Startup'),
    [Environment]::GetFolderPath('CommonStartup'),
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
)

foreach ($folder in $startupFolders) {
    if (-not (Test-Path $folder)) { continue }
    
    Write-Host "`nChecking: $folder" -ForegroundColor Cyan
    $items = Get-ChildItem -Path $folder -ErrorAction SilentlyContinue
    $removed = $false
    
    foreach ($item in $items) {
        if (Is-SafeItem $item.Name) {
            Write-Host "  - Keeping (safe): $($item.Name)" -ForegroundColor Cyan
            continue
        }
        
        try {
            Remove-Item -Path $item.FullName -Force -Recurse -ErrorAction Stop
            Write-Host "  - Removed: $($item.Name)" -ForegroundColor Green
            $removed = $true
        } catch {
            Write-Host "  ! Could not remove '$($item.Name)': $_" -ForegroundColor Red
        }
    }
    
    if (-not $removed) {
        Write-Host "  - No non-essential items found" -ForegroundColor Gray
    }
}

# 7. Clean Services
Write-Host "`n[4/4] Cleaning Non-Essential Services..." -ForegroundColor Yellow
$services = Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' }

foreach ($service in $services) {
    $serviceName = $service.DisplayName
    
    if (Is-SafeItem $serviceName) {
        Write-Host "  - Keeping (safe): $serviceName" -ForegroundColor Cyan
        continue
    }
    
    # Skip critical Windows services
    if ($serviceName -like "Windows*" -or $serviceName -like "Microsoft*" -or $serviceName -like "*Network*" -or $serviceName -like "*Update*") {
        Write-Host "  - Keeping (system): $serviceName" -ForegroundColor Cyan
        continue
    }
    
    try {
        Set-Service -Name $service.Name -StartupType Manual -ErrorAction Stop
        Write-Host "  - Set to manual: $serviceName" -ForegroundColor Green
    } catch {
        Write-Host "  ! Could not configure service '$serviceName': $_" -ForegroundColor Red
    }
}

# 8. Final instructions
Write-Host "`n=== ULTIMATE CLEANUP COMPLETE ===" -ForegroundColor Cyan
Write-Host "1. A SYSTEM RESTART IS REQUIRED for all changes to take effect."
Write-Host "2. After restart, check if the black screen issue is resolved."
Write-Host "3. If issues persist, consider these additional steps:"
Write-Host "   - Run System File Checker: sfc /scannow"
Write-Host "   - Run DISM: DISM /Online /Cleanup-Image /RestoreHealth"
Write-Host "   - Perform a clean boot for further diagnosis"
Write-Host "   - Check Event Viewer for system errors"

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
