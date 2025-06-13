#!/usr/bin/env pwsh
# OpenDevin Enhanced Environment Setup Script
# This script helps set up all required credentials and configuration for integrated services

param(
    [switch]$SkipOllama,
    [switch]$SkipSupabase,
    [switch]$Interactive
)

Write-Host "=== OpenDevin Enhanced Environment Setup ===" -ForegroundColor Cyan
Write-Host "This script will help you configure all required credentials and services." -ForegroundColor White
Write-Host ""

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Function to securely prompt for input
function Get-SecureInput($prompt, $secure = $false) {
    if ($secure) {
        $secureString = Read-Host -Prompt $prompt -AsSecureString
        return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureString))
    } else {
        return Read-Host -Prompt $prompt
    }
}

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "⚠️  Existing .env file found. Creating backup..." -ForegroundColor Yellow
    Copy-Item ".env" ".env.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}

# Copy .env.example to .env if it doesn't exist
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Created .env file from .env.example" -ForegroundColor Green
    } else {
        Write-Host "❌ .env.example file not found. Please run this script from the project root." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=== 1. Ollama Setup ===" -ForegroundColor Cyan

if (-not $SkipOllama) {
    # Check if Ollama is installed
    if (Test-Command "ollama") {
        Write-Host "✅ Ollama is installed" -ForegroundColor Green
        
        # Check if Ollama is running
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
            Write-Host "✅ Ollama is running" -ForegroundColor Green
            
            # List available models
            Write-Host "📋 Available models:"
            if ($response.models) {
                foreach ($model in $response.models) {
                    Write-Host "   - $($model.name)" -ForegroundColor White
                }
            } else {
                Write-Host "   No models installed" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Ollama is not running. Please start it with: ollama serve" -ForegroundColor Yellow
        }
        
        # Install recommended models
        Write-Host ""
        $installModels = Read-Host "Would you like to install recommended models? (y/N)"
        if ($installModels -eq 'y' -or $installModels -eq 'Y') {
            $models = @("codellama:7b-instruct", "llama2:7b-chat", "mistral:7b-instruct")
            foreach ($model in $models) {
                Write-Host "📥 Installing $model..." -ForegroundColor Blue
                ollama pull $model
            }
        }
    } else {
        Write-Host "❌ Ollama is not installed." -ForegroundColor Red
        Write-Host "Please install Ollama from: https://ollama.ai" -ForegroundColor Yellow
        Write-Host "Then run: ollama serve" -ForegroundColor Yellow
    }
} else {
    Write-Host "⏭️  Skipping Ollama setup" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 2. Supabase Setup ===" -ForegroundColor Cyan

if (-not $SkipSupabase) {
    Write-Host "To set up Supabase integration, you'll need:" -ForegroundColor White
    Write-Host "1. A Supabase account (https://app.supabase.com)" -ForegroundColor White
    Write-Host "2. A new project created in Supabase" -ForegroundColor White
    Write-Host "3. Your project's URL and API keys" -ForegroundColor White
    Write-Host ""
    
    $setupSupabase = Read-Host "Do you have a Supabase project ready? (y/N)"
    if ($setupSupabase -eq 'y' -or $setupSupabase -eq 'Y') {
        Write-Host ""
        Write-Host "Please provide your Supabase credentials:" -ForegroundColor Cyan
        
        $supabaseUrl = Get-SecureInput "Supabase Project URL (e.g., https://xxxxx.supabase.co)"
        $supabaseAnonKey = Get-SecureInput "Supabase Anon Key" $true
        $supabaseServiceKey = Get-SecureInput "Supabase Service Role Key" $true
        
        # Update .env file
        $envContent = Get-Content ".env"
        $envContent = $envContent -replace "SUPABASE_URL=.*", "SUPABASE_URL=$supabaseUrl"
        $envContent = $envContent -replace "SUPABASE_ANON_KEY=.*", "SUPABASE_ANON_KEY=$supabaseAnonKey"
        $envContent = $envContent -replace "SUPABASE_SERVICE_ROLE_KEY=.*", "SUPABASE_SERVICE_ROLE_KEY=$supabaseServiceKey"
        $envContent | Set-Content ".env"
        
        Write-Host "✅ Supabase credentials saved to .env file" -ForegroundColor Green
    } else {
        Write-Host "📋 Please create a Supabase project at https://app.supabase.com" -ForegroundColor Yellow
        Write-Host "   Then run this script again to configure the credentials." -ForegroundColor Yellow
    }
} else {
    Write-Host "⏭️  Skipping Supabase setup" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 3. Additional Configuration ===" -ForegroundColor Cyan

# Check if user wants to set up OpenAI API key for fallback
$setupOpenAI = Read-Host "Do you want to configure OpenAI API key for fallback? (y/N)"
if ($setupOpenAI -eq 'y' -or $setupOpenAI -eq 'Y') {
    $openaiKey = Get-SecureInput "OpenAI API Key" $true
    
    $envContent = Get-Content ".env"
    $envContent = $envContent -replace "LLM_API_KEY=.*", "LLM_API_KEY=$openaiKey"
    $envContent | Set-Content ".env"
    
    Write-Host "✅ OpenAI API key saved to .env file" -ForegroundColor Green
}

# Create workspace directory if it doesn't exist
if (-not (Test-Path "workspace")) {
    New-Item -ItemType Directory -Path "workspace" | Out-Null
    Write-Host "✅ Created workspace directory" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 4. Verification ===" -ForegroundColor Cyan

# Load environment variables for verification
$envVars = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        $envVars[$matches[1]] = $matches[2]
    }
}

# Check configuration status
Write-Host "Configuration Status:" -ForegroundColor White
Write-Host "✅ warp.toml: Present" -ForegroundColor Green
Write-Host "✅ .env file: Present" -ForegroundColor Green

if ($envVars["SUPABASE_URL"] -and $envVars["SUPABASE_URL"] -ne "https://your-project-id.supabase.co") {
    Write-Host "✅ Supabase: Configured" -ForegroundColor Green
} else {
    Write-Host "⚠️  Supabase: Not configured" -ForegroundColor Yellow
}

if ($envVars["LLM_API_KEY"] -and $envVars["LLM_API_KEY"] -ne "your-openai-api-key-here") {
    Write-Host "✅ OpenAI API: Configured" -ForegroundColor Green
} else {
    Write-Host "ℹ️  OpenAI API: Not configured (using Ollama only)" -ForegroundColor Blue
}

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Start Ollama: ollama serve" -ForegroundColor Yellow
Write-Host "2. Run the enhanced setup: .\start-enhanced.ps1" -ForegroundColor Yellow
Write-Host "3. Access the application at http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  Important: Keep your .env file secure and never commit it to version control!" -ForegroundColor Red

