# Application Uninstaller Script
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

function Show-Menu {
    param (
        [string]$Title = 'Application Uninstaller',
        [array]$Options
    )
    
    $selected = $false
    $selection = 0
    
    while (-not $selected) {
        Clear-Host
        Write-Host "===== $Title =====" -ForegroundColor Cyan
        Write-Host "Use UP/DOWN arrows to navigate, SPACE to select, ENTER to confirm selection"
        Write-Host "Selected applications will be marked with [X]"
        Write-Host "=========================================="
        
        for ($i = 0; $i -lt $Options.Count; $i++) {
            $prefix = if ($Options[$i].Selected) { "[X] " } else { "[ ] " }
            if ($i -eq $selection) {
                Write-Host ("--> " + $prefix + $Options[$i].DisplayName) -ForegroundColor Green
            } else {
                Write-Host ("    " + $prefix + $Options[$i].DisplayName)
            }
            
            # Show additional info for the selected item
            if ($i -eq $selection) {
                Write-Host ("    Version: " + $Options[$i].DisplayVersion) -ForegroundColor DarkGray
                Write-Host ("    Publisher: " + $Options[$i].Publisher) -ForegroundColor DarkGray
                Write-Host ""
            }
        }
        
        $key = $host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        switch ($key.VirtualKeyCode) {
            38 { # Up arrow
                if ($selection -gt 0) { $selection-- }
            }
            40 { # Down arrow
                if ($selection -lt ($Options.Count - 1)) { $selection++ }
            }
            32 { # Space
                $Options[$selection].Selected = -not $Options[$selection].Selected
            }
            13 { # Enter
                $selected = $true
            }
        }
    }
    
    return $Options | Where-Object { $_.Selected }
}

# Get all installed applications
Write-Host "Gathering installed applications..." -ForegroundColor Yellow
$uninstallKeys = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$apps = @()
foreach ($key in $uninstallKeys) {
    $apps += Get-ItemProperty -Path $key -ErrorAction SilentlyContinue | 
        Where-Object { $_.DisplayName -ne $null } |
        Select-Object @{
            Name = 'Selected'
            Expression = { $false }
        }, 
        DisplayName, 
        DisplayVersion, 
        Publisher,
        @{
            Name = 'UninstallString'
            Expression = { 
                if ($_.UninstallString) { 
                    $_.UninstallString -replace '"', '' 
                } else { 
                    $null 
                } 
            }
        },
        @{
            Name = 'QuietUninstallString'
            Expression = { 
                if ($_.QuietUninstallString) { 
                    $_.QuietUninstallString -replace '"', '' 
                } else { 
                    $null 
                } 
            }
        }
}

# Sort and filter out duplicates
$apps = $apps | Sort-Object -Property DisplayName -Unique

# Show menu and get selection
$selectedApps = Show-Menu -Title "Select Applications to Uninstall" -Options $apps

if ($selectedApps.Count -eq 0) {
    Write-Host "No applications selected for uninstallation." -ForegroundColor Yellow
    exit
}

# Confirm before uninstalling
Write-Host "`nThe following applications will be uninstalled:" -ForegroundColor Red
$selectedApps | ForEach-Object { 
    Write-Host ("- " + $_.DisplayName) -ForegroundColor Yellow
}

$confirm = Read-Host "`nAre you sure you want to continue? (Y/N)"
if ($confirm -ne "Y") {
    Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
    exit
}

# Uninstall selected applications
foreach ($app in $selectedApps) {
    Write-Host ("`nUninstalling " + $app.DisplayName + "...") -ForegroundColor Cyan
    
    try {
        $uninstallString = $null
        
        # Prefer quiet uninstall if available
        if ($app.QuietUninstallString) {
            $uninstallString = $app.QuietUninstallString
        } elseif ($app.UninstallString) {
            $uninstallString = $app.UninstallString
        }
        
        if ($uninstallString) {
            # Handle different uninstall string formats
            if ($uninstallString -match '^msiexec') {
                # MSI uninstall
                $msiArgs = $uninstallString -replace '^.*msiexec\s*', ''
                Start-Process "msiexec.exe" -ArgumentList "/x $msiArgs /qn /norestart" -Wait -NoNewWindow
            } else {
                # Standard uninstall string
                $uninstallCmd = $uninstallString -split ' ' | Select-Object -First 1
                $uninstallArgs = $uninstallString.Substring($uninstallCmd.Length).Trim()
                
                # Add silent uninstall parameters for common installers
                if ($uninstallCmd -like "*setup.exe" -or $uninstallCmd -like "*unins*.exe") {
                    $uninstallArgs += " /SILENT /NORESTART"
                }
                
                Start-Process -FilePath $uninstallCmd -ArgumentList $uninstallArgs -Wait -NoNewWindow
            }
            
            Write-Host ("Successfully uninstalled: " + $app.DisplayName) -ForegroundColor Green
        } else {
            Write-Host ("Could not find uninstall string for: " + $app.DisplayName) -ForegroundColor Red
        }
    } catch {
        Write-Host ("Error uninstalling " + $app.DisplayName + ": " + $_.Exception.Message) -ForegroundColor Red
    }
}

# Final message
Write-Host "`nUninstallation process completed." -ForegroundColor Cyan
Write-Host "Some applications may require a system restart to complete the uninstallation."
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
