# Simple PhotoPrism Deployment Script for PowerShell

# Create directories
New-Item -ItemType Directory -Force storage, originals, import, database

# Copy environment file
Copy-Item docker/.env.example docker/.env.prod -Force

# Pull Docker images
docker compose -f docker/docker-compose.prod.yml pull

# Start containers
docker compose -f docker/docker-compose.prod.yml up -d

Write-Host "PhotoPrism should be running at http://localhost:2342"
