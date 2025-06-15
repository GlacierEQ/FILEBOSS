#!/usr/bin/env bash

# Verifies the BRAINS integration in a Docker environment
set -e

echo "=== PhotoPrism BRAINS Integration Verification ==="

# Verify Docker environment
echo "Checking Docker installation..."
docker version --format '{{.Server.Version}}' || { echo "Docker not available"; exit 1; }
docker-compose version || { echo "Docker Compose not available"; exit 1; }

# Deploy test instance
echo "Deploying test instance with BRAINS enabled..."
cd "$(dirname "$0")/../docker"
cp docker-compose.yml docker-compose.test.yml
cp brains/docker-compose.override.yml docker-compose.override.yml
sed -i 's/image: photoprism\/photoprism:latest/build: ..\//' docker-compose.test.yml

# Start the containers
echo "Starting containers..."
docker-compose -f docker-compose.test.yml -f docker-compose.override.yml up -d

# Wait for the service to be ready
echo "Waiting for service to be ready..."
timeout 120 bash -c 'until curl -s http://localhost:2342/api/v1/status | grep -q "\"status\":\"operational\""; do sleep 2; done' || { echo "Service failed to become ready"; exit 1; }

# Test BRAINS endpoints
echo "Testing BRAINS endpoints..."
curl -s http://localhost:2342/api/v1/brains/status | grep -q "\"enabled\":true" || { echo "BRAINS not enabled"; exit 1; }

# Upload test photo
echo "Uploading test photo..."
curl -s -X POST -F "files=@../testdata/test.jpg" http://localhost:2342/api/v1/upload

# Trigger BRAINS analysis
echo "Triggering BRAINS analysis..."
curl -s -X POST -H "Content-Type: application/json" -d '{"force":true}' http://localhost:2342/api/v1/brains/analyze

# Wait for analysis to complete
echo "Waiting for analysis to complete..."
sleep 10

# Check if results are available
echo "Checking for analysis results..."
PHOTO_UID=$(curl -s http://localhost:2342/api/v1/photos | grep -o '"UID":"[^"]*"' | head -1 | cut -d'"' -f4)
if curl -s "http://localhost:2342/api/v1/brains/$PHOTO_UID" | grep -q '"available":true'; then
  echo "✅ BRAINS analysis results are available"
else
  echo "❌ BRAINS analysis failed"
  exit 1
fi

# Clean up
echo "Cleaning up..."
docker-compose -f docker-compose.test.yml -f docker-compose.override.yml down -v

echo "=== Verification completed successfully ==="
