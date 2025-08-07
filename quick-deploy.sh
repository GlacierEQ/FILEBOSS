#!/bin/bash
# CaseBuilder Quick Deploy Script
# One-command deployment for local development

set -e

echo "🚀 CaseBuilder Quick Deploy Starting..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./casebuilder.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
EOF
    echo "✅ .env file created"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run verification tests
echo "🧪 Running system verification..."
python test_casebuilder_verification.py

# Start with Docker Compose
echo "🐳 Starting Docker containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "❤️ Checking application health..."
curl -f http://localhost:8000/health || {
    echo "❌ Health check failed. Checking logs..."
    docker-compose logs
    exit 1
}

echo ""
echo "🎉 CaseBuilder deployed successfully!"
echo "=" * 50
echo "🌐 Application: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔄 Alternative Docs: http://localhost:8000/redoc"
echo "❤️ Health Check: http://localhost:8000/health"
echo "📊 System Info: http://localhost:8000/"
echo ""
echo "🛠️ Management Commands:"
echo "  docker-compose logs -f    # View logs"
echo "  docker-compose down       # Stop services"
echo "  docker-compose restart    # Restart services"
echo ""
echo "Ready for action! 🚀"