# SAFE BLOWTWARE REMOVER
# This script safely removes common bloatware while keeping essential system components
# Run as Administrator

$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

# Create system restore point
try {
    Write-Host "Creating system restore point..." -ForegroundColor Cyan
    Checkpoint-Computer -Description "Before Safe Bloatware Removal" -RestorePointType MODIFY_SETTINGS
    Write-Host "  - System restore point created successfully" -ForegroundColor Green
} catch {
    Write-Host "  ! Could not create system restore point: $_" -ForegroundColor Red
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y") { exit }
}

# Common bloatware patterns to remove (case insensitive)
$bloatwarePatterns = @(
    # Common bloatware
    "*Bonjour*",
    "*CCleaner*",
    "*iTunes*",
    "*QuickTime*",
    "*3D Vision*",
    "*HP *",
    "*Dell *",
    "*Lenovo *",
    "*Acer *",
    "*ASUS *",
    "*Samsung *",
    "*McAfee*",
    "*Norton *",
    "*NVIDIA 3D*",
    "*Java*Update*",
    "*Java(TM) 6*",
    "*Java(TM) 7*",
    "*Java(TM) 8*",
    "*Java Auto Updater*",
    "*Adobe Reader*",
    "*Acrobat Reader*",
    "*Microsoft OneDrive*",
    "*Microsoft Teams*",
    "*Xbox*",
    "*Candy Crush*",
    "*Spotify*",
    "*Netflix*",
    "*Facebook*",
    "*Instagram*",
    "*Twitter*",
    "*TikTok*",
    "*McAfee*",
    "*Norton*",
    "*AVG*",
    "*Avast*",
    "*Bing*",
    "*Cortana*",
    "*Skype*",
    "*OneDrive*",
    "*Microsoft Edge*"
)

# Essential patterns to keep (never remove these)
$essentialPatterns = @(
    "*Windows*",
    "*Microsoft Visual C++*",
    "*.NET*Framework*",
    "*NVIDIA*Driver*",
    "*NVIDIA*Graphics*",
    "*NVIDIA*PhysX*",
    "*Intel*",
    "*Realtek*",
    "*AMD*",
    "*Security*",
    "*Defender*",
    "*Update*",
    "*Driver*",
    "*Firmware*",
    "*BIOS*",
    "*Chipset*"
)

function Get-InstalledPrograms {
    $uninstallKeys = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    
    $programs = @()
    
    foreach ($key in $uninstallKeys) {
        $programs += Get-ItemProperty -Path $key -ErrorAction SilentlyContinue | 
            Where-Object { $_.DisplayName -ne $null } |
            Select-Object @{
                Name = 'DisplayName'
                Expression = { $_.DisplayName.Trim() }
            }, 
            @{
                Name = 'UninstallString'
                Expression = { if ($_.UninstallString) { $_.UninstallString.Trim() -replace '"', '' } else { $null } }
            },
            @{
                Name = 'QuietUninstallString'
                Expression = { if ($_.QuietUninstallString) { $_.QuietUninstallString.Trim() -replace '"', '' } else { $null } }
            },
            @{
                Name = 'IsBloatware'
                Expression = { $false }
            }
    }
    
    return $programs | Sort-Object -Property DisplayName -Unique
}

function Test-IsBloatware {
    param (
        [string]$displayName
    )
    
    # Skip empty or system components
    if ([string]::IsNullOrWhiteSpace($displayName)) {
        return $false
    }
    
    # Check against essential patterns (never remove these)
    foreach ($pattern in $essentialPatterns) {
        if ($displayName -like $pattern) {
            return $false
        }
    }
    
    # Check against bloatware patterns
    foreach ($pattern in $bloatwarePatterns) {
        if ($displayName -like $pattern) {
            return $true
        }
    }
    
    return $false
}

function Uninstall-Program {
    param (
        [string]$displayName,
        [string]$uninstallString,
        [string]$quietUninstallString
    )
    
    Write-Host "`nUninstalling: $displayName" -ForegroundColor Cyan
    
    try {
        $uninstallCmd = $null
        $args = $null
        
        # Prefer quiet uninstall if available
        if ($quietUninstallString) {
            $uninstallString = $quietUninstallString
        }
        
        if ($uninstallString -match '^msiexec') {
            # MSI uninstall
            $msiArgs = $uninstallString -replace '^.*msiexec\s*', ''
            $uninstallCmd = "msiexec.exe"
            $args = "/x $msiArgs /qn /norestart"
        } else {
            # Standard uninstall string
            $parts = $uninstallString -split ' ' | Where-Object { $_ -ne '' }
            $uninstallCmd = $parts[0]
            $args = $uninstallString.Substring($uninstallCmd.Length).Trim()
            
            # Add silent uninstall parameters for common installers
            if ($uninstallCmd -like "*setup.exe" -or $uninstallCmd -like "*unins*.exe") {
                $args += " /SILENT /NORESTART"
            }
        }
        
        if (Test-Path $uninstallCmd) {
            Write-Host "  Running: $uninstallCmd $args" -ForegroundColor DarkGray
            $process = Start-Process -FilePath $uninstallCmd -ArgumentList $args -Wait -NoNewWindow -PassThru
            
            if ($process.ExitCode -eq 0) {
                Write-Host "  Successfully uninstalled: $displayName" -ForegroundColor Green
                return $true
            } else {
                Write-Host "  Uninstall completed with exit code: $($process.ExitCode)" -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "  Could not find uninstaller: $uninstallCmd" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  Error uninstalling $displayName : $_" -ForegroundColor Red
        return $false
    }
}

# Main script execution
Write-Host "=== SAFE BLOWTWARE REMOVER ===" -ForegroundColor Cyan
Write-Host "This script will remove common bloatware while keeping essential system components.`n"

# Get all installed programs
Write-Host "Scanning installed programs..." -ForegroundColor Yellow
$programs = Get-InstalledPrograms

# Identify bloatware
$bloatware = @()
foreach ($program in $programs) {
    if (Test-IsBloatware -displayName $program.DisplayName) {
        $program.IsBloatware = $true
        $bloatware += $program
    }
}

# Show bloatware found
if ($bloatware.Count -eq 0) {
    Write-Host "No bloatware detected!" -ForegroundColor Green
    exit
}

Write-Host "`nThe following bloatware was detected:" -ForegroundColor Yellow
$bloatware | ForEach-Object { Write-Host ("- " + $_.DisplayName) -ForegroundColor Yellow }

# Confirm before uninstalling
$confirm = Read-Host "`nDo you want to uninstall these programs? (Y/N)"
if ($confirm -ne "Y") {
    Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
    exit
}

# Uninstall bloatware
$successCount = 0
$failCount = 0

foreach ($app in $bloatware) {
    if (Uninstall-Program -displayName $app.DisplayName -uninstallString $app.UninstallString -quietUninstallString $app.QuietUninstallString) {
        $successCount++
    } else {
        $failCount++
    }
}

# Show summary
Write-Host "`n=== UNINSTALLATION SUMMARY ===" -ForegroundColor Cyan
Write-Host "Successfully uninstalled: $successCount programs" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "Failed to uninstall: $failCount programs" -ForegroundColor Red
}

# Final recommendations
Write-Host "`n=== RECOMMENDATIONS ===" -ForegroundColor Cyan
Write-Host "1. Restart your computer to complete uninstallation"
Write-Host "2. Run Windows Update to install any available updates"
Write-Host "3. Consider using a disk cleanup tool to remove temporary files"

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
