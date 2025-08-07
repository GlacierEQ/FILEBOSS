# SafeCleanup.psm1
# Shared helpers to add safety, logging, and idempotency to cleanup scripts

Set-StrictMode -Version Latest

# region: Globals
$script:TranscriptStarted = $false
# endregion

function Assert-Admin() {
    [CmdletBinding()]
    param()

    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This action requires elevation. Re-run the script in an Administrator PowerShell session."
    }
}

function Start-SafeTranscript {
    [CmdletBinding()]
    param(
        [Parameter()]
        [string]$Directory = "$env:ProgramData\SafeCleanup\Logs",
        [Parameter()]
        [string]$Prefix = "SafeCleanup"
    )
    if ($script:TranscriptStarted) { return }
    try {
        if (-not (Test-Path -LiteralPath $Directory)) {
            New-Item -ItemType Directory -Path $Directory -Force | Out-Null
        }
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $logPath = Join-Path $Directory "$Prefix-$timestamp.log"
        Start-Transcript -Path $logPath -ErrorAction Stop | Out-Null
        $script:TranscriptStarted = $true
        Write-Verbose "Transcript started at: $logPath"
    } catch {
        Write-Warning "Failed to start transcript: $_"
    }
}

function Stop-SafeTranscript {
    [CmdletBinding()]
    param()
    if ($script:TranscriptStarted) {
        try {
            Stop-Transcript | Out-Null
        } catch {
            Write-Warning "Failed to stop transcript: $_"
        } finally {
            $script:TranscriptStarted = $false
        }
    }
}

function Confirm-Destructive {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [switch]$Force
    )
    if ($Force.IsPresent) { return $true }
    $answer = Read-Host "$Message (Y/N)"
    return ($answer -match '^[Yy]$')
}

function Invoke-IfNotWhatIf {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)]
        [scriptblock]$Action,
        [string]$Target = "operation"
    )
    if ($PSCmdlet.ShouldProcess($Target)) {
        & $Action
    } else {
        Write-Verbose "WhatIf: would run action on $Target"
    }
}

function Remove-ItemSafe {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [switch]$Recurse,
        [switch]$Force
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Verbose "Skip remove (not found): $Path"
        return
    }
    $target = "Remove-Item $Path"
    Invoke-IfNotWhatIf -Target $target -Action {
        try {
            Remove-Item -LiteralPath $Path -ErrorAction Stop -Force:$Force.IsPresent -Recurse:$Recurse.IsPresent
            Write-Host "  - Removed: $Path" -ForegroundColor Green
        } catch {
            Write-Warning "  ! Failed to remove $Path : $_"
        }
    }
}

function Remove-ItemPropertySafe {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [string]$Name,
        [switch]$Force
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Verbose "Registry path not found: $Path"
        return
    }
    try {
        $key = Get-Item -LiteralPath $Path -ErrorAction Stop
        $names = $key.GetValueNames()
        if ($names -notcontains $Name) {
            Write-Verbose "Registry value not present: $Path :: $Name"
            return
        }
    } catch {
        Write-Warning "Failed probing registry: $Path :: $Name :: $_"
        return
    }

    $target = "Remove-ItemProperty $Path::$Name"
    Invoke-IfNotWhatIf -Target $target -Action {
        try {
            Remove-ItemProperty -Path $Path -Name $Name -Force:$Force.IsPresent -ErrorAction Stop
            Write-Host "  - Removed from $Path: $Name" -ForegroundColor Green
        } catch {
            Write-Warning "  ! Failed to remove '$Name' from $Path : $_"
        }
    }
}

function Disable-ScheduledTaskSafe {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)] [string]$TaskName
    )
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    } catch {
        Write-Verbose "Scheduled task not found: $TaskName"
        return
    }

    if ($task.State -eq "Disabled") {
        Write-Verbose "Task already disabled: $TaskName"
        return
    }

    $target = "Disable-ScheduledTask $TaskName"
    Invoke-IfNotWhatIf -Target $target -Action {
        try {
            $task | Disable-ScheduledTask -ErrorAction Stop | Out-Null
            Write-Host "  - Disabled task: $TaskName" -ForegroundColor Green
        } catch {
            Write-Warning "  ! Could not disable task '$TaskName': $_"
        }
    }
}

function Set-ServiceStartupManualSafe {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)] [string]$ServiceName
    )
    try {
        $svc = Get-Service -Name $ServiceName -ErrorAction Stop
    } catch {
        Write-Verbose "Service not found: $ServiceName"
        return
    }

    if ($svc.StartType -eq 'Manual') {
        Write-Verbose "Service already Manual: $ServiceName"
        return
    }

    $target = "Set-Service -Name $ServiceName -StartupType Manual"
    Invoke-IfNotWhatIf -Target $target -Action {
        try {
            Set-Service -Name $ServiceName -StartupType Manual -ErrorAction Stop
            Write-Host "  - Set to manual: $($svc.DisplayName)" -ForegroundColor Green
        } catch {
            Write-Warning "  ! Could not configure service '$($svc.DisplayName)': $_"
        }
    }
}

Export-ModuleMember -Function *-Safe, Assert-Admin, Start-SafeTranscript, Stop-SafeTranscript, Confirm-Destructive, Invoke-IfNotWhatIf
