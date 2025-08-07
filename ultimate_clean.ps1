<#
.SYNOPSIS
    Performs an aggressive but safe cleanup of system startup processes.

.DESCRIPTION
    This script systematically disables non-essential startup items from the Task Scheduler, Registry, Startup Folders, and Services. It preserves a list of known-good system-critical items to prevent system instability. A system restore point is created before any changes are made.

.NOTES
    Author: Omni-Cognitive Operator
    Version: 2.0
    Requires: Administrator privileges
#>

function Test-IsAdmin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function New-SystemRestorePoint {
    param(
        [string]$Description = "Before Ultimate Startup Cleanup"
    )
    try {
        Write-Host "Creating system restore point..." -ForegroundColor Cyan
        Checkpoint-Computer -Description $Description -RestorePointType MODIFY_SETTINGS
        Write-Host "  - System restore point created successfully." -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ! Could not create system restore point: $_" -ForegroundColor Red
        return $false
    }
}

function Test-IsSafeToModify {
    param(
        [string]$ItemName,
        [string[]]$SafeList
    )
    foreach ($safe in $SafeList) {
        if ($ItemName -like "*$safe*") { return $true }
    }
    return $false
}

function Clean-ScheduledTasks {
    param(
        [string[]]$SafeList
    )
    Write-Host "`n[1/4] Cleaning Task Scheduler..." -ForegroundColor Yellow
    Get-ScheduledTask | Where-Object { $_.State -ne "Disabled" } | ForEach-Object {
        if (Test-IsSafeToModify -ItemName $_.TaskName -SafeList $SafeList -or $_.TaskPath -like "\Microsoft\*") {
            Write-Host "  - Keeping (safe/system): $($_.TaskName)" -ForegroundColor Cyan
        } else {
            try {
                $_ | Disable-ScheduledTask -ErrorAction Stop
                Write-Host "  - Disabled: $($_.TaskName)" -ForegroundColor Green
            } catch {
                Write-Host "  ! Could not disable task '$($_.TaskName)': $_" -ForegroundColor Red
            }
        }
    }
}

function Clean-RegistryKeys {
    param(
        [string[]]$SafeList
    )
    Write-Host "`n[2/4] Cleaning Registry..." -ForegroundColor Yellow
    $regPaths = @(
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
    )
    foreach ($path in $regPaths) {
        if (-not (Test-Path $path)) { continue }
        Get-Item -Path $path | Get-ItemProperty | Select-Object -ExpandProperty PSObject | Select-Object -ExpandProperty Properties | ForEach-Object {
            if (-not (Test-IsSafeToModify -ItemName $_.Name -SafeList $SafeList)) {
                try {
                    Remove-ItemProperty -Path $path -Name $_.Name -Force -ErrorAction Stop
                    Write-Host "  - Removed registry item: $($_.Name)" -ForegroundColor Green
                } catch {
                    Write-Host "  ! Could not remove registry item '$($_.Name)': $_" -ForegroundColor Red
                }
            }
        }
    }
}

function Clean-StartupFolders {
    param(
        [string[]]$SafeList
    )
    Write-Host "`n[3/4] Cleaning Startup Folders..." -ForegroundColor Yellow
    $startupFolders = @(
        [Environment]::GetFolderPath('Startup'),
        [Environment]::GetFolderPath('CommonStartup')
    )
    foreach ($folder in $startupFolders) {
        if (-not (Test-Path $folder)) { continue }
        Get-ChildItem -Path $folder | ForEach-Object {
            if (-not (Test-IsSafeToModify -ItemName $_.Name -SafeList $SafeList)) {
                try {
                    Remove-Item -Path $_.FullName -Force -Recurse -ErrorAction Stop
                    Write-Host "  - Removed from startup: $($_.Name)" -ForegroundColor Green
                } catch {
                    Write-Host "  ! Could not remove '$($_.Name)': $_" -ForegroundColor Red
                }
            }
        }
    }
}

function Clean-Services {
    param(
        [string[]]$SafeList
    )
    Write-Host "`n[4/4] Setting non-essential services to Manual..." -ForegroundColor Yellow
    Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' } | ForEach-Object {
        if (-not (Test-IsSafeToModify -ItemName $_.DisplayName -SafeList $SafeList) -and $_.Name -notlike "*wuauserv*") {
            try {
                Set-Service -Name $_.Name -StartupType Manual -ErrorAction Stop
                Write-Host "  - Set to manual: $($_.DisplayName)" -ForegroundColor Green
            } catch {
                Write-Host "  ! Could not configure service '$($_.DisplayName)': $_" -ForegroundColor Red
            }
        }
    }
}

function Main {
    if (-not (Test-IsAdmin)) {
        Write-Warning "This script requires Administrator privileges. Please re-run as Administrator."
        return
    }

    if (-not (New-SystemRestorePoint)) {
        $response = Read-Host "Failed to create a restore point. Continue at your own risk? (Y/N)"
        if ($response -ne 'Y') { return }
    }

    $safeToKeepPatterns = @(
        "Windows", "Microsoft", "NVIDIA", "Intel", "Realtek", "AMD", "Synaptics", "SecurityHealth", "RtkAudUService"
    )

    Clean-ScheduledTasks -SafeList $safeToKeepPatterns
    Clean-RegistryKeys -SafeList $safeToKeepPatterns
    Clean-StartupFolders -SafeList $safeToKeepPatterns
    Clean-Services -SafeList $safeToKeepPatterns

    Write-Host "`n=== ULTIMATE CLEANUP COMPLETE ===" -ForegroundColor Cyan
    Write-Host "A system restart is required for all changes to take effect."
}

Main
