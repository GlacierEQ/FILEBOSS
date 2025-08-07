# CaseBuilder Quick Deploy Script for Windows
# PowerShell deployment script

Write-Host "🚀 CaseBuilder Quick Deploy Starting..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    @"
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./casebuilder.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ .env file created" -ForegroundColor Green
}

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run verification tests
Write-Host "🧪 Running system verification..." -ForegroundColor Yellow
python test_casebuilder_verification.py

# Start with Docker Compose
Write-Host "🐳 Starting Docker containers..." -ForegroundColor Yellow
docker-compose up --build -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check health
Write-Host "❤️ Checking application health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check passed!" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Health check failed. Checking logs..." -ForegroundColor Red
    docker-compose logs
    exit 1
}

Write-Host ""
Write-Host "🎉 CaseBuilder deployed successfully!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host "🌐 Application: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔄 Alternative Docs: http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host "❤️ Health Check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "📊 System Info: http://localhost:8000/" -ForegroundColor Cyan
Write-Host ""
Write-Host "🛠️ Management Commands:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f    # View logs"
Write-Host "  docker-compose down       # Stop services"
Write-Host "  docker-compose restart    # Restart services"
Write-Host ""
Write-Host "Ready for action! 🚀" -ForegroundColor Green

# Open browser
Write-Host "🌐 Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:8000/docs"