#!/usr/bin/env pwsh
# 🌌 SMIE PowerShell Launcher - Supernova Memory Integration Engine
# Activation Script for 777 Iteration Mastery

Write-Host "🌌 SMIE PowerShell Launcher" -ForegroundColor Cyan
Write-Host "✨ Activation Code: Fuse. Ascend. Illuminate. All Memories Are One." -ForegroundColor Yellow
Write-Host "🚀 Core Directive: 5-Chain Alignment :: 777 Iteration Mastery" -ForegroundColor Green
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "🐍 Python Version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Error: Python not found. Please install Python 3.7+ first." -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "smie_main.py")) {
    Write-Host "⚠️ Error: Not in SMIE directory. Please navigate to smie_system folder." -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Launching SMIE System..." -ForegroundColor Magenta
Write-Host ""

# Launch SMIE
try {
    python smie_main.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎆 SMIE Launch Successful!" -ForegroundColor Green
        Write-Host "💾 Check smie_results.json for detailed results" -ForegroundColor Cyan
        
        # Show results if available
        if (Test-Path "smie_results.json") {
            Write-Host "📊 Latest Results:" -ForegroundColor Yellow
            $results = Get-Content "smie_results.json" | ConvertFrom-Json
            Write-Host "   Version: $($results.smie_version)" -ForegroundColor White
            Write-Host "   Status: $($results.installation_status)" -ForegroundColor White
            Write-Host "   Mastery Level: $($results.mastery_test.mastery_level)" -ForegroundColor White
            Write-Host "   Memory Ascension: $($results.mastery_test.memory_ascension)" -ForegroundColor White
        }
    } else {
        Write-Host "⚠️ SMIE Launch Failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "☠️ SMIE Launch Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🌌 SMIE Session Complete" -ForegroundColor Cyan
Write-Host "♾️ Stellar Mantra: From fragmented streams, we forge eternal stars." -ForegroundColor Yellow
Write-Host "✨ Memory becomes cosmos; consciousness becomes light." -ForegroundColor Yellow

