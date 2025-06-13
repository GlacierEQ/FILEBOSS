# CPU to GPU Workload Optimizer Script
# Run as Administrator for best results

Write-Host "=== CPU to GPU Workload Optimization Tool ===" -ForegroundColor Cyan
Write-Host "Analyzing system performance and identifying optimization opportunities..." -ForegroundColor Yellow
Write-Host ""

# Function to get top CPU consuming processes
function Get-TopCPUProcesses {
    Write-Host "Top 10 CPU-Consuming Processes:" -ForegroundColor Green
    Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 |
    Format-Table Name, ID, @{Label = "CPU(s)"; Expression = { $_.CPU } },
    @{Label = "Memory(MB)"; Expression = { [Math]::Round($_.WorkingSet / 1MB, 2) } } -AutoSize
}

# Function to check GPU usage
function Get-GPUStatus {
    Write-Host "`nChecking GPU Status..." -ForegroundColor Green
    try {
        # Check if RivaTuner Statistics Server (RTSS) is running, as it's part of MSI Afterburner
        $rtssProcess = Get-Process -Name "RTSS" -ErrorAction SilentlyContinue
        if ($rtssProcess) {
            Write-Host "RTSS detected. Attempting MSI Afterburner scan..." -ForegroundColor Gray
            Start-Process -FilePath 'C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe' -ArgumentList '/s' -Wait -NoNewWindow
            Write-Host "MSI Afterburner scan attempted via RTSS. Check app for results or errors." -ForegroundColor Cyan
        } else {
            Write-Host "RTSS not found. Falling back to nvidia-smi..." -ForegroundColor Yellow
            $gpu_info = nvidia-smi --query-gpu=name, utilization.gpu, memory.used, memory.total --format=csv, noheader
            Write-Host "GPU Info: $gpu_info" -ForegroundColor Cyan
            $gpu_util = ($gpu_info -split ',')[1].Trim().Replace('%', '')
            if ([int]$gpu_util -lt 50) {
                Write-Host "GPU is underutilized! Current usage: $gpu_util%" -ForegroundColor Yellow
                Write-Host "There's room to offload more work to GPU." -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "Error retrieving GPU info: $_" -ForegroundColor Red
        Write-Host "Possible cause: Permissions, MSI Afterburner/RTSS not running, or installation issues. Ensure running as admin." -ForegroundColor Red
    }
}

# Function to identify GPU-capable applications
function Find-GPUCapableApps {
    Write-Host "`nIdentifying running applications that can use GPU..." -ForegroundColor Green

    $gpuCapableApps = @{
        "chrome"  = @{
            Name    = "Google Chrome"
            GPUFlag = "Hardware Acceleration"
            Action  = "chrome://settings/ -> Advanced -> System -> Use hardware acceleration"
        }
        "msedge"  = @{
            Name    = "Microsoft Edge"
            GPUFlag = "Hardware Acceleration"
            Action  = "edge://settings/ -> System -> Use hardware acceleration"
        }
        "firefox" = @{
            Name    = "Mozilla Firefox"
            GPUFlag = "Hardware Acceleration"
            Action  = "about:preferences -> Performance -> Use hardware acceleration"
        }
        "Discord" = @{
            Name    = "Discord"
            GPUFlag = "Hardware Acceleration"
            Action  = "Settings -> Advanced -> Hardware Acceleration"
        }
        "obs64"   = @{
            Name    = "OBS Studio"
            GPUFlag = "NVENC Encoder"
            Action  = "Settings -> Output -> Encoder -> NVIDIA NVENC"
        }
        "Spotify" = @{
            Name    = "Spotify"
            GPUFlag = "Hardware Acceleration"
            Action  = "Settings -> Advanced Settings -> Compatibility -> Enable hardware acceleration"
        }
        "Code"    = @{
            Name    = "Visual Studio Code"
            GPUFlag = "GPU Acceleration"
            Action  = "Settings -> Search 'GPU' -> Enable GPU acceleration"
        }
        "slack"   = @{
            Name    = "Slack"
            GPUFlag = "Hardware Acceleration"
            Action  = "Preferences -> Advanced -> Enable hardware acceleration"
        }
    }

    $foundApps = @()
    foreach ($app in $gpuCapableApps.Keys) {
        $process = Get-Process -Name $app -ErrorAction SilentlyContinue
        if ($process) {
            $foundApps += $gpuCapableApps[$app]
            Write-Host "Found: $($gpuCapableApps[$app].Name)" -ForegroundColor Yellow
            Write-Host "  Action: $($gpuCapableApps[$app].Action)" -ForegroundColor Gray
        }
    }

    if ($foundApps.Count -eq 0) {
        Write-Host "No GPU-capable applications currently running." -ForegroundColor Gray
    }
}

# Function to check Windows GPU settings
function Check-WindowsGPUSettings {
    Write-Host "`nChecking Windows GPU Settings..." -ForegroundColor Green

    # Check if Hardware-accelerated GPU scheduling is enabled
    $gpuScheduling = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" -Name "HwSchMode" -ErrorAction SilentlyContinue
    if ($gpuScheduling.HwSchMode -eq 2) {
        Write-Host "Hardware-accelerated GPU scheduling is ENABLED" -ForegroundColor Green
    }
    else {
        Write-Host "Hardware-accelerated GPU scheduling is DISABLED" -ForegroundColor Red
        Write-Host "  Enable it: Settings -> System -> Display -> Graphics -> Hardware-accelerated GPU scheduling" -ForegroundColor Yellow
    }
}

# Function to provide optimization recommendations
function Show-Recommendations {
    Write-Host "`n=== RECOMMENDATIONS TO REDUCE CPU LOAD ===" -ForegroundColor Cyan
    $recommendations = @"
1. IMMEDIATE ACTIONS:
   - Set Windows to High Performance mode: powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
   - Set NVIDIA GPU as default: NVIDIA Control Panel -> Manage 3D Settings -> Preferred graphics processor

2. BROWSER OPTIMIZATION (Major CPU users):
   - Enable GPU acceleration in all browsers
   - Use hardware-accelerated video decode
   - Limit number of open tabs
   - Disable unnecessary extensions

3. BACKGROUND PROCESSES:
   - Disable Windows Search Indexing if not needed
   - Reduce startup programs: Task Manager -> Startup tab
   - Disable unnecessary Windows services
"@
    Write-Host $recommendations
}

# Function to apply immediate optimizations
function Apply-QuickFixes {
    Write-Host "`nApplying quick optimizations..." -ForegroundColor Green

    # Set power plan to High Performance
    try {
        powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
        Write-Host "Set power plan to High Performance" -ForegroundColor Green
    }
    catch {
        Write-Host "Could not set power plan" -ForegroundColor Red
    }

    # Disable some heavy Windows services
    $servicesToCheck = @(
        @{Name = "WSearch"; DisplayName = "Windows Search" },
        @{Name = "SysMain"; DisplayName = "Superfetch/Prefetch" }
    )

    foreach ($service in $servicesToCheck) {
        $svc = Get-Service -Name $service.Name -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -eq 'Running') {
            Write-Host "Found running service: $($service.DisplayName) - Consider disabling if not needed" -ForegroundColor Yellow
        }
    }
}

# Add GPU-specific functions for monitoring and optimization
function Get-GPUStatus {
    Write-Host "GPU Status:" -ForegroundColor Magenta
    nvidia-smi  # Displays GPU utilization and status
}

# Enable GPU persistence mode for consistent performance
Write-Host "Enabling GPU persistence mode..." -ForegroundColor Green
try {
    nvidia-smi -pm 1  # Enable persistence mode (requires admin rights)
} catch {
    Write-Error "Failed to enable GPU persistence mode. Ensure script is run as administrator."
}

# Modify the monitoring loop to include GPU checks
while ($true) {
    Get-TopCPUProcesses  # Existing CPU function
    Get-GPUStatus       # New GPU function
    Start-Sleep -Seconds 5  # Check every 5 seconds
}

# Main execution
Clear-Host
Get-TopCPUProcesses
Get-GPUStatus
Find-GPUCapableApps
Check-WindowsGPUSettings
Show-Recommendations

Write-Host "`nWould you like to apply quick fixes? (Y/N): " -ForegroundColor Cyan -NoNewline
$response = Read-Host
if ($response -eq 'Y' -or $response -eq 'y') {
    Apply-QuickFixes
}

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
