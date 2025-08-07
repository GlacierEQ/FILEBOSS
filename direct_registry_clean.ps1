<#
.SYNOPSIS
    A modular script to remove persistent startup items from the registry, scheduled tasks, and startup folders.

.DESCRIPTION
    This script provides a safe and structured way to clean up unwanted startup applications by targeting specific patterns. It requires administrative privileges to modify system-wide settings.

.NOTES
    Author: Omni-Cognitive Operator
    Version: 2.0
    Requires: Administrator privileges
#>

function Test-IsAdmin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remove-RegistryStartupItems {
    param(
        [string[]]$TargetPatterns
    )
    $registryPaths = @(
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce"
    )

    foreach ($path in $registryPaths) {
        if (-not (Test-Path $path)) { continue }
        Get-Item -Path $path | Get-ItemProperty | Select-Object -ExpandProperty PSObject | Select-Object -ExpandProperty Properties | ForEach-Object {
            foreach ($pattern in $TargetPatterns) {
                if ($_.Name -like "*$pattern*") {
                    try {
                        Remove-ItemProperty -Path $path -Name $_.Name -Force -ErrorAction Stop
                        Write-Host "  - Removed registry item: $($_.Name) from $path" -ForegroundColor Green
                    } catch {
                        Write-Host "  ! Failed to remove registry item: $($_.Name) from $path. Error: $_" -ForegroundColor Red
                    }
                }
            }
        }
    }
}

function Disable-ScheduledStartupTasks {
    param(
        [string[]]$TargetPatterns
    )
    foreach ($pattern in $TargetPatterns) {
        Get-ScheduledTask | Where-Object { $_.TaskName -like "*$pattern*" -and $_.State -ne "Disabled" } | ForEach-Object {
            try {
                $_ | Disable-ScheduledTask -ErrorAction Stop
                Write-Host "  - Disabled scheduled task: $($_.TaskName)" -ForegroundColor Green
            } catch {
                Write-Host "  ! Could not disable task: $($_.TaskName). Error: $_" -ForegroundColor Red
            }
        }
    }
}

function Clear-StartupFolders {
    param(
        [string[]]$TargetPatterns
    )
    $startupFolders = @(
        [Environment]::GetFolderPath('Startup'),
        [Environment]::GetFolderPath('CommonStartup')
    )

    foreach ($folder in $startupFolders) {
        if (-not (Test-Path $folder)) { continue }
        Get-ChildItem -Path $folder | ForEach-Object {
            $item = $_.Name
            foreach ($pattern in $TargetPatterns) {
                if ($item -like "*$pattern*") {
                    try {
                        Remove-Item -Path $_.FullName -Force -Recurse -ErrorAction Stop
                        Write-Host "  - Removed from startup folder: $item" -ForegroundColor Green
                    } catch {
                        Write-Host "  ! Could not remove '$item' from startup. Error: $_" -ForegroundColor Red
                    }
                }
            }
        }
    }
}

function Main {
    if (-not (Test-IsAdmin)) {
        Write-Warning "This script requires Administrator privileges. Please re-run as Administrator."
        return
    }

    $targetItems = @(
        "GoogleDriveFS", "Razer", "RazerAxon", "RazerCortex", "ChatGPT", "Ollama", "podman"
    )

    Write-Host "Initiating direct startup cleanup protocol..." -ForegroundColor Cyan
    
    Write-Host "`n[1/3] Cleaning registry startup items..." -ForegroundColor Yellow
    Remove-RegistryStartupItems -TargetPatterns $targetItems

    Write-Host "`n[2/3] Disabling scheduled startup tasks..." -ForegroundColor Yellow
    Disable-ScheduledStartupTasks -TargetPatterns $targetItems

    Write-Host "`n[3/3] Clearing startup folders..." -ForegroundColor Yellow
    Clear-StartupFolders -TargetPatterns $targetItems

    Write-Host "`n=== DIRECT STARTUP CLEANUP COMPLETE ===" -ForegroundColor Cyan
    Write-Host "A system restart is recommended to ensure all changes take effect."
}

Main
