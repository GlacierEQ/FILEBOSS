# System Optimization and Startup Repair Script
# This script disables problematic startup items and optimizes system performance

# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== FILEBOSS System Optimizer ===" -ForegroundColor Cyan
Write-Host "Initializing maximum performance mode..."

# 1. Disable problematic startup applications
$problematicApps = @(
    "Razer Axon",
    "Razer App Engine",
    "Razer Cortex",
    "Amazon Photos",
    "Comet",
    "Discord",
    "Spotify",
    "Steam"
)

Write-Host "`n[1/3] Disabling problematic startup applications..." -ForegroundColor Yellow

# Disable from Task Scheduler
foreach ($app in $problematicApps) {
    try {
        $task = Get-ScheduledTask | Where-Object { $_.TaskName -like "*$app*" -and $_.State -ne "Disabled" }
        if ($task) {
            $task | Disable-ScheduledTask -ErrorAction SilentlyContinue
            Write-Host "  - Disabled scheduled task: $($task.TaskName)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ! Could not disable scheduled task for $app: $_" -ForegroundColor Red
    }
}

# Disable from Registry (Current User)
$regPaths = @(
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
)

foreach ($path in $regPaths) {
    if (Test-Path $path) {
        $regKey = Get-Item -Path $path
        foreach ($app in $problematicApps) {
            $regKey.GetValueNames() | Where-Object { $_ -like "*$app*" } | ForEach-Object {
                try {
                    Remove-ItemProperty -Path $path -Name $_ -Force -ErrorAction Stop
                    Write-Host "  - Removed from $path: $_" -ForegroundColor Green
                } catch {
                    Write-Host "  ! Could not remove $app from $path: $_" -ForegroundColor Red
                }
            }
        }
    }
}

# 2. Optimize system performance
Write-Host "`n[2/3] Optimizing system performance..." -ForegroundColor Yellow

# Set power plan to High Performance
try {
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  # High Performance GUID
    Write-Host "  - Power plan set to High Performance" -ForegroundColor Green
} catch {
    Write-Host "  ! Could not set power plan: $_" -ForegroundColor Red
}

# Disable visual effects for better performance
$visualEffects = @(
    "MenuShowDelay",
    "DragFullWindows",
    "FontSmoothing",
    "AnimateWindows"
)

foreach ($effect in $visualEffects) {
    try {
        Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name $effect -Value "0" -ErrorAction Stop
        Write-Host "  - Disabled visual effect: $effect" -ForegroundColor Green
    } catch {
        Write-Host "  ! Could not disable $effect: $_" -ForegroundColor Red
    }
}

# 3. Clean up temporary files
Write-Host "`n[3/3] Cleaning up temporary files..." -ForegroundColor Yellow

$tempFolders = @(
    "$env:TEMP\*",
    "$env:WINDIR\Temp\*",
    "$env:LOCALAPPDATA\Temp\*"
)

foreach ($folder in $tempFolders) {
    try {
        Remove-Item -Path $folder -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  - Cleaned temp files in: $folder" -ForegroundColor Green
    } catch {
        Write-Host "  ! Could not clean $folder: $_" -ForegroundColor Red
    }
}

# 4. Final steps and user instructions
Write-Host "`n=== Optimization Complete ===" -ForegroundColor Cyan
Write-Host "1. A system restart is recommended to apply all changes."
Write-Host "2. If you still experience the black screen, try booting into Safe Mode"
Write-Host "   and running this script again with the -SafeMode parameter."
Write-Host "3. For persistent issues, check the Windows Event Viewer for errors."

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
