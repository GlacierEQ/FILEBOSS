#!/bin/bash
set -e

# Simple PhotoPrism Deployment Script - No frills, just works
echo "=== PhotoPrism Simple Deployment ==="

# Environment file setup
ENV_FILE="docker/.env.prod"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating environment file from example..."
    cp docker/.env.example "$ENV_FILE"
fi

# Make sure directories exist
mkdir -p storage originals import database

# Stop any existing containers
echo "Stopping any existing PhotoPrism containers..."
docker compose -f docker/docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# Pull latest images
echo "Pulling latest Docker images..."
docker compose -f docker/docker-compose.prod.yml pull

# Launch containers
echo "Starting PhotoPrism containers..."
docker compose -f docker/docker-compose.prod.yml up -d

# Verify startup
echo "Verifying deployment..."
sleep 10
if docker compose -f docker/docker-compose.prod.yml ps | grep -q "photoprism_brains.*Up"; then
    echo "✓ BRAINS service started successfully"
else
    echo "⚠ BRAINS service may not have started properly. Checking logs:"
    docker compose -f docker/docker-compose.prod.yml logs brains
fi

if docker compose -f docker/docker-compose.prod.yml ps | grep -q "photoprism.*Up"; then
    echo "✓ PhotoPrism started successfully"
    
    # Extract site URL from environment
    SITE_URL=$(grep PHOTOPRISM_SITE_URL "$ENV_FILE" | cut -d '=' -f2)
    if [ -z "$SITE_URL" ]; then
        SITE_URL="http://localhost:2342"
    fi
    
    echo ""
    echo "🎉 PhotoPrism is now running!"
    echo "📷 Access your photo library at: $SITE_URL"
    echo "👤 Default username: admin"
    echo "🔑 Default password: insecure (change this immediately!)"
    echo ""
else
    echo "⚠ PhotoPrism may not have started properly. Checking logs:"
    docker compose -f docker/docker-compose.prod.yml logs photoprism
fi

echo "=== Deployment Complete ==="
