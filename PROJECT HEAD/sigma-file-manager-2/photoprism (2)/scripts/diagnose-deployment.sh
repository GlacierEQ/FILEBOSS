#!/bin/bash
set -e

# Simple diagnostic script for PhotoPrism deployment
echo "=== PhotoPrism Deployment Diagnostics ==="
echo "Checking Docker installation..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
else
    echo "✓ Docker is installed"
    docker --version
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed or not in PATH"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
else
    echo "✓ Docker Compose is installed"
    docker compose version 2>/dev/null || docker-compose --version
fi

# Check environment file
if [ ! -f "docker/.env.prod" ]; then
    echo "WARNING: Production environment file not found"
    echo "Creating from example..."
    cp docker/.env.example docker/.env.prod
    echo "✓ Created docker/.env.prod from example"
else
    echo "✓ Environment file exists"
fi

# Check disk space
echo "Checking disk space..."
df -h .

# Check Docker status
echo "Checking Docker service status..."
if systemctl is-active docker &> /dev/null || docker info &> /dev/null; then
    echo "✓ Docker service is running"
else
    echo "ERROR: Docker service is not running"
    echo "Try starting Docker with: sudo systemctl start docker"
fi

# Show existing containers
echo "Current Docker containers:"
docker ps -a

echo "=== Diagnostics Complete ==="
echo "If you're still having issues, try the simple deployment script."
