#!/usr/bin/env pwsh
# OpenDevin Enhanced Setup Verification Script
# This script verifies that all components are properly configured and running

param(
    [switch]$Detailed
)

Write-Host "=== OpenDevin Enhanced Setup Verification ===" -ForegroundColor Cyan
Write-Host "Checking configuration and service status..." -ForegroundColor White
Write-Host ""

$global:issues = @()
$global:warnings = @()

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to add issue
function Add-Issue($message) {
    $global:issues += $message
    Write-Host "❌ $message" -ForegroundColor Red
}

# Function to add warning
function Add-Warning($message) {
    $global:warnings += $message
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

# Function to show success
function Show-Success($message) {
    Write-Host "✅ $message" -ForegroundColor Green
}

# Function to show info
function Show-Info($message) {
    Write-Host "ℹ️  $message" -ForegroundColor Blue
}

Write-Host "=== 1. File Structure Check ===" -ForegroundColor Cyan

# Check required files
if (Test-Path "warp.toml") {
    Show-Success "warp.toml found"
} else {
    Add-Issue "warp.toml not found"
}

if (Test-Path ".env.example") {
    Show-Success ".env.example found"
} else {
    Add-Issue ".env.example not found"
}

if (Test-Path ".env") {
    Show-Success ".env file found"
} else {
    Add-Warning ".env file not found - run setup-environment.ps1"
}

if (Test-Path "supabase-schema.sql") {
    Show-Success "supabase-schema.sql found"
} else {
    Add-Warning "supabase-schema.sql not found"
}

if (Test-Path "workspace") {
    Show-Success "workspace directory found"
} else {
    Add-Warning "workspace directory not found"
    New-Item -ItemType Directory -Path "workspace" -Force | Out-Null
    Show-Info "Created workspace directory"
}

Write-Host ""
Write-Host "=== 2. Environment Variables Check ===" -ForegroundColor Cyan

if (Test-Path ".env") {
    $envVars = @{}
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $envVars[$matches[1]] = $matches[2]
        }
    }
    
    # Check Supabase configuration
    if ($envVars["SUPABASE_URL"] -and $envVars["SUPABASE_URL"] -ne "https://your-project-id.supabase.co") {
        Show-Success "Supabase URL configured"
        if ($Detailed) {
            Show-Info "URL: $($envVars['SUPABASE_URL'])"
        }
    } else {
        Add-Warning "Supabase URL not configured"
    }
    
    if ($envVars["SUPABASE_ANON_KEY"] -and $envVars["SUPABASE_ANON_KEY"] -ne "your-supabase-anon-key") {
        Show-Success "Supabase Anon Key configured"
    } else {
        Add-Warning "Supabase Anon Key not configured"
    }
    
    if ($envVars["SUPABASE_SERVICE_ROLE_KEY"] -and $envVars["SUPABASE_SERVICE_ROLE_KEY"] -ne "your-supabase-service-role-key") {
        Show-Success "Supabase Service Role Key configured"
    } else {
        Add-Warning "Supabase Service Role Key not configured"
    }
    
    # Check LLM configuration
    if ($envVars["LLM_MODEL"]) {
        Show-Success "LLM Model configured: $($envVars['LLM_MODEL'])"
    } else {
        Add-Warning "LLM Model not configured"
    }
    
    if ($envVars["LLM_BASE_URL"]) {
        Show-Success "LLM Base URL configured: $($envVars['LLM_BASE_URL'])"
    } else {
        Add-Warning "LLM Base URL not configured"
    }
} else {
    Add-Issue "Cannot check environment variables - .env file not found"
}

Write-Host ""
Write-Host "=== 3. Ollama Service Check ===" -ForegroundColor Cyan

if (Test-Command "ollama") {
    Show-Success "Ollama CLI installed"
    
    # Check if Ollama is running
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
        Show-Success "Ollama service is running"
        
        if ($response.models -and $response.models.Count -gt 0) {
            Show-Success "$($response.models.Count) models available"
            if ($Detailed) {
                foreach ($model in $response.models) {
                    Show-Info "  - $($model.name) (Modified: $($model.modified))"
                }
            }
        } else {
            Add-Warning "No models installed"
        }
    } catch {
        Add-Issue "Ollama service not responding on localhost:11434"
        Show-Info "Try running: ollama serve"
    }
} else {
    Add-Issue "Ollama not installed or not in PATH"
    Show-Info "Install from: https://ollama.ai"
}

Write-Host ""
Write-Host "=== 4. Supabase Connection Check ===" -ForegroundColor Cyan

if (Test-Path ".env") {
    $envVars = @{}
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $envVars[$matches[1]] = $matches[2]
        }
    }
    
    if ($envVars["SUPABASE_URL"] -and $envVars["SUPABASE_URL"] -ne "https://your-project-id.supabase.co") {
        try {
            $url = "$($envVars['SUPABASE_URL'])/rest/v1/"
            $headers = @{
                "apikey" = $envVars["SUPABASE_ANON_KEY"]
                "Authorization" = "Bearer $($envVars['SUPABASE_ANON_KEY'])"
            }
            
            $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get -TimeoutSec 10
            Show-Success "Supabase API connection successful"
        } catch {
            Add-Warning "Supabase API connection failed: $($_.Exception.Message)"
            Show-Info "Check your Supabase credentials and network connection"
        }
    } else {
        Add-Warning "Cannot test Supabase connection - URL not configured"
    }
} else {
    Add-Warning "Cannot test Supabase connection - .env file not found"
}

Write-Host ""
Write-Host "=== 5. Python Dependencies Check ===" -ForegroundColor Cyan

if (Test-Command "python") {
    Show-Success "Python found"
    $pythonVersion = python --version 2>&1
    if ($Detailed) {
        Show-Info "Version: $pythonVersion"
    }
    
    # Check if virtual environment is active
    if ($env:VIRTUAL_ENV) {
        Show-Success "Virtual environment active: $env:VIRTUAL_ENV"
    } else {
        Add-Warning "No virtual environment detected"
        Show-Info "Consider using: python -m venv venv; .\venv\Scripts\Activate"
    }
} else {
    Add-Issue "Python not found in PATH"
}

if (Test-Path "pyproject.toml") {
    Show-Success "pyproject.toml found"
} else {
    Add-Warning "pyproject.toml not found"
}

Write-Host ""
Write-Host "=== 6. Node.js Dependencies Check ===" -ForegroundColor Cyan

if (Test-Command "node") {
    Show-Success "Node.js found"
    $nodeVersion = node --version 2>&1
    if ($Detailed) {
        Show-Info "Version: $nodeVersion"
    }
} else {
    Add-Issue "Node.js not found in PATH"
}

if (Test-Command "npm") {
    Show-Success "npm found"
    $npmVersion = npm --version 2>&1
    if ($Detailed) {
        Show-Info "Version: $npmVersion"
    }
} else {
    Add-Warning "npm not found in PATH"
}

if (Test-Path "frontend\package.json") {
    Show-Success "Frontend package.json found"
    
    if (Test-Path "frontend\node_modules") {
        Show-Success "Frontend dependencies installed"
    } else {
        Add-Warning "Frontend dependencies not installed"
        Show-Info "Run: cd frontend && npm install"
    }
} else {
    Add-Warning "Frontend package.json not found"
}

Write-Host ""
Write-Host "=== 7. Docker Check (Optional) ===" -ForegroundColor Cyan

if (Test-Command "docker") {
    Show-Success "Docker found"
    
    try {
        $dockerVersion = docker --version 2>&1
        if ($Detailed) {
            Show-Info "Version: $dockerVersion"
        }
        
        # Check if Docker is running
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Show-Success "Docker service is running"
        } else {
            Add-Warning "Docker service not running"
        }
    } catch {
        Add-Warning "Docker installed but not accessible"
    }
} else {
    Show-Info "Docker not found (optional for enhanced features)"
}

Write-Host ""
Write-Host "=== Verification Summary ===" -ForegroundColor Cyan

if ($global:issues.Count -eq 0 -and $global:warnings.Count -eq 0) {
    Write-Host "🎉 Perfect! All components are properly configured." -ForegroundColor Green
    Write-Host "Your OpenDevin Enhanced setup is ready to go!" -ForegroundColor Green
} elseif ($global:issues.Count -eq 0) {
    Write-Host "✅ Good! Setup is functional with minor warnings." -ForegroundColor Yellow
    Write-Host "Address warnings for optimal experience." -ForegroundColor Yellow
} else {
    Write-Host "❌ Issues found that need attention:" -ForegroundColor Red
    foreach ($issue in $global:issues) {
        Write-Host "   • $issue" -ForegroundColor Red
    }
}

if ($global:warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Warnings:" -ForegroundColor Yellow
    foreach ($warning in $global:warnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan

if ($global:issues.Count -gt 0) {
    Write-Host "1. Resolve the issues listed above" -ForegroundColor White
    Write-Host "2. Run setup-environment.ps1 if needed" -ForegroundColor White
    Write-Host "3. Re-run this verification script" -ForegroundColor White
} else {
    Write-Host "1. Start Ollama: ollama serve" -ForegroundColor White
    Write-Host "2. Run the application: .\start-enhanced.ps1" -ForegroundColor White
    Write-Host "3. Access at: http://localhost:3000" -ForegroundColor White
}

Write-Host ""
Write-Host "For detailed setup instructions, see: ENVIRONMENT_SETUP.md" -ForegroundColor Blue

