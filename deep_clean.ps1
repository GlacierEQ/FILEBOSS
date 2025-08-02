# Deep Clean Startup Items
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

# Create a system restore point
try {
    Write-Host "Creating system restore point..." -ForegroundColor Cyan
    Checkpoint-Computer -Description "Before Deep Clean Script" -RestorePointType MODIFY_SETTINGS
    Write-Host "  - System restore point created successfully" -ForegroundColor Green
} catch {
    Write-Host "  ! Could not create system restore point: $_" -ForegroundColor Red
}

# List of items to keep (system critical)
$safeItems = @(
    "Windows Defender",
    "SecurityHealth"
)

# List of known problematic items to remove
$problematicItems = @(
    "Razer",
    "Google Drive",
    "EPPCCMON",
    "Stickies",
    "Cortex",
    "Axon",
    "Discord",
    "Spotify",
    "Steam",
    "4-Organizer",
    "ChatGPT",
    "mymap",
    "Ollama",
    "podman"
)

# Function to check if an item is safe
function Is-SafeItem($itemName) {
    foreach ($safe in $safeItems) {
        if ($itemName -like "*$safe*") {
            return $true
        }
    }
    return $false
}

# Function to check if an item should be removed
function Should-RemoveItem($itemName) {
    foreach ($problem in $problematicItems) {
        if ($itemName -like "*$problem*") {
            return $true
        }
    }
    return $false
}

# 1. Clean Task Scheduler
Write-Host "`n[1/4] Cleaning Task Scheduler..." -ForegroundColor Yellow
$tasks = Get-ScheduledTask | Where-Object { $_.State -ne "Disabled" -and $_.TaskPath -notlike "\Microsoft\*" }

foreach ($task in $tasks) {
    $taskName = $task.TaskName
    
    if (Is-SafeItem $taskName) {
        Write-Host "  - Keeping (safe): $taskName" -ForegroundColor Cyan
        continue
    }
    
    if (Should-RemoveItem $taskName) {
        try {
            $task | Disable-ScheduledTask -ErrorAction Stop
            Write-Host "  - Disabled: $taskName" -ForegroundColor Green
        } catch {
            Write-Host "  ! Could not disable task '$taskName': $_" -ForegroundColor Red
        }
    }
}

# 2. Clean Registry
Write-Host "`n[2/4] Cleaning Registry..." -ForegroundColor Yellow
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
                if (-not (Is-SafeItem $value) -and (Should-RemoveItem $value)) {
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
            if (-not (Is-SafeItem $itemName) -and (Should-RemoveItem $itemName)) {
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

# 4. Clean Services
Write-Host "`n[4/4] Cleaning Non-Essential Services..." -ForegroundColor Yellow
$services = Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' }

foreach ($service in $services) {
    $serviceName = $service.DisplayName
    if (-not (Is-SafeItem $serviceName) -and (Should-RemoveItem $serviceName)) {
        try {
            Set-Service -Name $service.Name -StartupType Manual -ErrorAction Stop
            Write-Host "  - Set to manual: $serviceName" -ForegroundColor Green
        } catch {
            Write-Host "  ! Could not configure service '$serviceName': $_" -ForegroundColor Red
        }
    }
}

# Final Instructions
Write-Host "`n=== Deep Clean Complete ===" -ForegroundColor Cyan
Write-Host "1. A system restart is HIGHLY RECOMMENDED to apply all changes."
Write-Host "2. The black screen issue should now be resolved."
Write-Host "3. If issues persist, you can restore the system using the restore point we created."
Write-Host "   To restore: Press Win+R, type 'rstrui.exe', and follow the wizard."

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
