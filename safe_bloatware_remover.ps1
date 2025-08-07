<#
.SYNOPSIS
    Safely removes common bloatware from a Windows system.

.DESCRIPTION
    This script identifies and uninstalls common bloatware applications while ensuring essential system components are preserved. It creates a system restore point before making changes and provides a summary of the uninstallation process.

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
        [string]$Description = "Before Safe Bloatware Removal"
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

function Get-InstalledSoftware {
    $registryPaths = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    Get-ItemProperty -Path $registryPaths -ErrorAction SilentlyContinue | 
        Where-Object { $_.DisplayName -and $_.UninstallString } |
        Select-Object DisplayName, UninstallString, QuietUninstallString
}

function Test-IsBloatware {
    param(
        [string]$DisplayName,
        [string[]]$BloatwarePatterns,
        [string[]]$EssentialPatterns
    )

    foreach ($pattern in $EssentialPatterns) {
        if ($DisplayName -like $pattern) { return $false }
    }

    foreach ($pattern in $BloatwarePatterns) {
        if ($DisplayName -like $pattern) { return $true }
    }

    return $false
}

function Remove-Software {
    param(
        [Parameter(Mandatory=$true)]
        [string]$DisplayName,
        [Parameter(Mandatory=$true)]
        [string]$UninstallString,
        [string]$QuietUninstallString
    )

    Write-Host "`nAttempting to uninstall: $DisplayName" -ForegroundColor Cyan
    $uninstallCommand = $QuietUninstallString -or $UninstallString

    try {
        if ($uninstallCommand -match "msiexec") {
            $guid = $uninstallCommand -replace ".*\{(.*)\}.*", '$1'
            $arguments = "/x {$guid} /qn /norestart"
            $command = "msiexec.exe"
        } else {
            $command = $uninstallCommand.Split(' ')[0]
            $arguments = $uninstallCommand.Substring($command.Length).Trim() + " /S /SILENT /VERYSILENT /QUIET /NORESTART"
        }

        if (Test-Path $command) {
            Write-Host "  Executing: $command $arguments" -ForegroundColor DarkGray
            $process = Start-Process -FilePath $command -ArgumentList $arguments -Wait -PassThru -ErrorAction Stop
            if ($process.ExitCode -eq 0) {
                Write-Host "  Successfully uninstalled." -ForegroundColor Green
            } else {
                Write-Host "  Uninstalled with exit code: $($process.ExitCode). Manual removal may be required." -ForegroundColor Yellow
            }
        } else {
            Write-Host "  Uninstaller not found at path: $command" -ForegroundColor Red
        }
    } catch {
        Write-Host "  An error occurred during uninstallation: $_" -ForegroundColor Red
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

    $bloatwarePatterns = @(
        "*3D Viewer*", "*Cortana*", "*HP *", "*Dell *", "*Lenovo *", "*McAfee*", "*Norton*", 
        "*OneDrive*", "*Skype*", "*Spotify*", "*Xbox*", "*Your Phone*", "*Mixed Reality Portal*"
    )
    $essentialPatterns = @(
        "*Windows*", "*Microsoft Visual C++*", "*.NET*", "*NVIDIA*Driver*", "*Intel*Driver*", 
        "*Realtek*", "*AMD*Driver*", "*Security*", "*Update*", "*Driver*"
    )

    Write-Host "Scanning for bloatware..." -ForegroundColor Yellow
    $installedSoftware = Get-InstalledSoftware
    $bloatwareToRemove = $installedSoftware | Where-Object { Test-IsBloatware -DisplayName $_.DisplayName -BloatwarePatterns $bloatwarePatterns -EssentialPatterns $essentialPatterns }

    if ($bloatwareToRemove.Count -eq 0) {
        Write-Host "No bloatware detected." -ForegroundColor Green
        return
    }

    Write-Host "Detected the following bloatware:" -ForegroundColor Yellow
    $bloatwareToRemove.DisplayName | ForEach-Object { Write-Host "- $_" }

    $response = Read-Host "`nProceed with uninstallation? (Y/N)"
    if ($response -ne 'Y') { return }

    foreach ($app in $bloatwareToRemove) {
        Remove-Software -DisplayName $app.DisplayName -UninstallString $app.UninstallString -QuietUninstallString $app.QuietUninstallString
    }

    Write-Host "`nBloatware removal process complete." -ForegroundColor Cyan
    Write-Host "It is recommended to restart your computer."
}

Main
