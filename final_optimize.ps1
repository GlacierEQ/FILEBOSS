# FINAL SYSTEM OPTIMIZATION SCRIPT
# Run as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "=== FINAL SYSTEM OPTIMIZATION ===" -ForegroundColor Cyan
Write-Host "This script will perform final system optimizations.\n"

# 1. Disk Cleanup
Write-Host "[1/4] Running Disk Cleanup..." -ForegroundColor Yellow
$tempFolders = @(
    "$env:TEMP\*",
    "$env:WINDIR\Temp\*",
    "$env:LOCALAPPDATA\Temp\*",
    "$env:USERPROFILE\AppData\Local\Microsoft\Windows\WER\*",
    "$env:USERPROFILE\AppData\Local\CrashDumps\*"
)

foreach ($folder in $tempFolders) {
    try {
        Remove-Item -Path $folder -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  - Cleaned: $folder" -ForegroundColor Green
    } catch {
        Write-Host "  ! Could not clean $folder : $_" -ForegroundColor Red
    }
}

# 2. System File Checker
Write-Host "`n[2/4] Running System File Checker..." -ForegroundColor Yellow
try {
    $result = Start-Process -FilePath "sfc" -ArgumentList "/scannow" -Wait -NoNewWindow -PassThru -ErrorAction Stop
    if ($result.ExitCode -eq 0) {
        Write-Host "  - No integrity violations found" -ForegroundColor Green
    } else {
        Write-Host "  - System File Checker found and fixed issues. Reboot recommended." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ! Error running System File Checker: $_" -ForegroundColor Red
}

# 3. DISM Health Check
Write-Host "`n[3/4] Running DISM Health Check..." -ForegroundColor Yellow
try {
    Write-Host "  - Checking system health..."
    $dism = Start-Process -FilePath "DISM" -ArgumentList "/Online /Cleanup-Image /CheckHealth" -Wait -NoNewWindow -PassThru -ErrorAction Stop
    if ($dism.ExitCode -eq 0) {
        Write-Host "  - System image health verified" -ForegroundColor Green
    } else {
        Write-Host "  - Running repair..."
        $repair = Start-Process -FilePath "DISM" -ArgumentList "/Online /Cleanup-Image /RestoreHealth" -Wait -NoNewWindow -PassThru -ErrorAction Stop
        if ($repair.ExitCode -eq 0) {
            Write-Host "  - System image repaired successfully" -ForegroundColor Green
        } else {
            Write-Host "  ! Could not repair system image" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "  ! Error running DISM: $_" -ForegroundColor Red
}

# 4. Check for Windows Updates
Write-Host "`n[4/4] Checking for Windows Updates..." -ForegroundColor Yellow
try {
    $updateSession = New-Object -ComObject Microsoft.Update.Session
    $updateSearcher = $updateSession.CreateUpdateSearcher()
    $searchResult = $updateSearcher.Search("IsInstalled=0 and IsHidden=0")
    
    if ($searchResult.Updates.Count -gt 0) {
        Write-Host "  - Found $($searchResult.Updates.Count) available updates" -ForegroundColor Yellow
        $updateSession = New-Object -ComObject Microsoft.Update.Session
        $updates = $searchResult.Updates
        $updatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
        
        foreach ($update in $updates) {
            Write-Host "    - $($update.Title)" -ForegroundColor Cyan
            $updatesToInstall.Add($update) | Out-Null
        }
        
        $installer = $updateSession.CreateUpdateInstaller()
        $installer.Updates = $updatesToInstall
        $installationResult = $installer.Install()
        
        if ($installationResult.ResultCode -eq 2) {
            Write-Host "  - Updates installed successfully. A restart may be required." -ForegroundColor Green
        } else {
            Write-Host "  - Updates were not installed. Result code: $($installationResult.ResultCode)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  - No new updates available" -ForegroundColor Green
    }
} catch {
    Write-Host "  ! Error checking for updates: $_" -ForegroundColor Red
}

# 5. Optional: Disable specific startup items
Write-Host "`n[Optional] Managing Startup Items..." -ForegroundColor Yellow

# Uncomment and modify these lines if you want to disable specific items
# Disable-StartupItem -Name "GoogleDriveFS"
# Disable-StartupItem -Name "Intel Processor Identification Utility"

# 6. Final Recommendations
Write-Host "`n=== OPTIMIZATION COMPLETE ===" -ForegroundColor Cyan
Write-Host "1. A system restart is recommended to apply all changes."
Write-Host "2. Consider these additional optimizations:"
Write-Host "   - Run disk defragmentation (if using HDD)"
Write-Host "   - Review installed programs and remove unused applications"
Write-Host "   - Consider using a good quality antivirus if not already in use"

# Pause to show completion
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
