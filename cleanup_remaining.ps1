# Cleanup Remaining Startup Items
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== Cleaning Up Remaining Startup Items ===" -ForegroundColor Cyan

# List of problematic items to remove
$itemsToRemove = @(
    @{Name="GoogleDriveFS"; Path="C:\Program Files\Google\Drive File Stream"},
    @{Name="EPPCCMON"; Path="C:\Program Files (x86)\EPSON Software\Epson Printer Connection Checker"},
    @{Name="RazerCortex"; Path="C:\Program Files (x86)\Razer\Razer Cortex"},
    @{Name="Stickies"; Path="C:\PROGRA~2\Stickies"}
)

# 1. Disable from Task Scheduler
Write-Host "`n[1/3] Disabling from Task Scheduler..." -ForegroundColor Yellow
foreach ($item in $itemsToRemove) {
    try {
        $task = Get-ScheduledTask | Where-Object { $_.TaskName -like "*$($item.Name)*" -and $_.State -ne "Disabled" }
        if ($task) {
            $task | Disable-ScheduledTask -ErrorAction SilentlyContinue
            Write-Host "  - Disabled scheduled task: $($task.TaskName)" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ! Could not disable scheduled task for $($item.Name): $_" -ForegroundColor Red
    }
}

# 2. Remove from Registry
Write-Host "`n[2/3] Removing from Registry..." -ForegroundColor Yellow
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
            foreach ($item in $itemsToRemove) {
                $regKey.GetValueNames() | Where-Object { $_ -like "*$($item.Name)*" } | ForEach-Object {
                    try {
                        Remove-ItemProperty -Path $path -Name $_ -Force -ErrorAction Stop
                        Write-Host "  - Removed from $path: $_" -ForegroundColor Green
                    } catch {
                        Write-Host "  ! Could not remove $($item.Name) from $path: $_" -ForegroundColor Red
                    }
                }
            }
        }
    }
}

# 3. Disable Startup Folder items
Write-Host "`n[3/3] Checking Startup Folders..." -ForegroundColor Yellow
$startupFolders = @(
    [Environment]::GetFolderPath('Startup'),
    [Environment]::GetFolderPath('CommonStartup')
)

foreach ($folder in $startupFolders) {
    if (Test-Path $folder) {
        foreach ($item in $itemsToRemove) {
            try {
                $files = Get-ChildItem -Path $folder -Filter "*$($item.Name)*" -ErrorAction SilentlyContinue
                foreach ($file in $files) {
                    try {
                        Remove-Item -Path $file.FullName -Force -ErrorAction Stop
                        Write-Host "  - Removed from $folder: $($file.Name)" -ForegroundColor Green
                    } catch {
                        Write-Host "  ! Could not remove $($file.Name) from $folder: $_" -ForegroundColor Red
                    }
                }
            } catch {
                Write-Host "  ! Error accessing $folder: $_" -ForegroundColor Red
            }
        }
    }
}

Write-Host "`n=== Cleanup Complete ===" -ForegroundColor Cyan
Write-Host "1. A system restart is recommended to ensure all changes take effect."
Write-Host "2. The black screen issue should now be resolved."
Write-Host "3. If issues persist, try booting into Safe Mode and running this script again."

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
