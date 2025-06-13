#!/usr/bin/env pwsh
<#
.SYNOPSIS
Quick start script for Enhanced OpenDevin

.DESCRIPTION
This script sets up and starts the enhanced OpenDevin installation with Ollama and Supabase integration.

.PARAMETER Mode
Specifies the mode to run: 'setup', 'start', 'stop', or 'status'

.EXAMPLE
./start-enhanced.ps1 -Mode setup
./start-enhanced.ps1 -Mode start
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('setup', 'start', 'stop', 'status', 'logs')]
    [string]$Mode = 'start'
)

# Enhanced OpenDevin Management Script
Write-Host "🚀 Enhanced OpenDevin Manager" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Yellow
Write-Host "=" * 40

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Blue
    
    # Check Docker
    try {
        docker --version | Out-Null
        Write-Host "✅ Docker is available" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker is not available" -ForegroundColor Red
        return $false
    }
    
    # Check Docker Compose
    try {
        docker-compose --version | Out-Null
        Write-Host "✅ Docker Compose is available" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker Compose is not available" -ForegroundColor Red
        return $false
    }
    
    return $true
}

function Start-Setup {
    Write-Host "⚙️ Running initial setup..." -ForegroundColor Blue
    
    # Run Python setup script
    if (Test-Path "setup-enhanced.py") {
        python setup-enhanced.py
    }
    
    # Create workspace if it doesn't exist
    if (!(Test-Path "workspace")) {
        New-Item -ItemType Directory -Name "workspace" | Out-Null
        Write-Host "✅ Created workspace directory" -ForegroundColor Green
    }
    
    # Pull and start services
    Write-Host "📦 Pulling Docker images..." -ForegroundColor Blue
    docker-compose -f docker-compose.enhanced.yml pull
    
    # Download models
    Write-Host "🤖 Downloading AI models..." -ForegroundColor Blue
    docker-compose -f docker-compose.enhanced.yml --profile setup up model-setup
    
    Write-Host "✅ Setup complete!" -ForegroundColor Green
}

function Start-Services {
    Write-Host "🚀 Starting Enhanced OpenDevin services..." -ForegroundColor Blue
    
    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Write-Host "⚠️ .env file not found. Creating default..." -ForegroundColor Yellow
        Start-Setup
    }
    
    # Start services
    docker-compose -f docker-compose.enhanced.yml up -d
    
    # Wait a moment for services to start
    Start-Sleep -Seconds 5
    
    # Check service status
    Show-Status
    
    Write-Host "" 
    Write-Host "🎉 Enhanced OpenDevin is starting up!" -ForegroundColor Green
    Write-Host "🔗 Access the interface at: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🤖 Ollama API at: http://localhost:11434" -ForegroundColor Cyan
    Write-Host "" 
    Write-Host "💡 Use './start-enhanced.ps1 -Mode logs' to view logs" -ForegroundColor Yellow
}

function Stop-Services {
    Write-Host "🛑 Stopping Enhanced OpenDevin services..." -ForegroundColor Blue
    docker-compose -f docker-compose.enhanced.yml down
    Write-Host "✅ Services stopped" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Service Status:" -ForegroundColor Blue
    docker-compose -f docker-compose.enhanced.yml ps
    
    # Check if OpenDevin is responding
    Write-Host "" 
    Write-Host "🔍 Health Checks:" -ForegroundColor Blue
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ OpenDevin UI is responding" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ OpenDevin UI is not responding" -ForegroundColor Red
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Ollama API is responding" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ Ollama API is not responding" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "📋 Showing service logs..." -ForegroundColor Blue
    docker-compose -f docker-compose.enhanced.yml logs -f
}

# Main execution
if (!(Test-Prerequisites)) {
    Write-Host "❌ Prerequisites check failed. Please install Docker and Docker Compose." -ForegroundColor Red
    exit 1
}

switch ($Mode) {
    'setup' { Start-Setup }
    'start' { Start-Services }
    'stop' { Stop-Services }
    'status' { Show-Status }
    'logs' { Show-Logs }
    default { Start-Services }
}

Write-Host "" 
Write-Host "=" * 40
Write-Host "✨ Enhanced OpenDevin Manager Complete" -ForegroundColor Cyan

