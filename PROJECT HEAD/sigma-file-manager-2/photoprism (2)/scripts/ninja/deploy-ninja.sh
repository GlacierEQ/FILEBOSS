#!/bin/bash
set -e

# PhotoPrism Ninja Deployment Script
# This script automates the deployment of PhotoPrism built with Ninja

# Default configuration
DOCKER_COMPOSE_FILE="docker/docker-compose.prod.yml"
ENV_FILE="docker/.env.prod"
BACKUP_DIR="storage/backup/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="deploy_ninja_$(date +%Y%m%d_%H%M%S).log"
BUILD_TYPE=${1:-release}
BUILD_DIR="build"

# Function to log messages
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to validate environment
validate_environment() {
  log "Validating environment..."
  
  # Check if Docker is installed
  if ! command -v docker &> /dev/null; then
    log "ERROR: Docker not found. Please install Docker first."
    exit 1
  fi
  
  # Check if Docker Compose is installed
  if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    log "ERROR: Docker Compose not found. Please install Docker Compose first."
    exit 1
  fi
  
  # Check if Ninja is installed
  if ! command -v ninja &> /dev/null; then
    log "WARNING: Ninja build system not found. Will skip custom build."
  fi
  
  # Check if environment file exists
  if [ ! -f "$ENV_FILE" ]; then
    log "WARNING: Environment file $ENV_FILE not found. Creating from example..."
    cp docker/.env.example "$ENV_FILE"
  fi

  log "Environment validation complete."
}

# Function to build the application using Ninja
build_application() {
  if command -v ninja &> /dev/null; then
    log "Building application with Ninja..."
    ./scripts/ninja/build-ninja.sh "$BUILD_TYPE" photoprism
    
    if [ -f "$BUILD_DIR/photoprism" ]; then
      log "Build successful."
      # Copy binary to Docker context
      cp "$BUILD_DIR/photoprism" docker/photoprism/
      log "Binary copied to Docker context."
    else
      log "WARNING: Build failed or binary not found. Will use Docker image instead."
    fi
  else
    log "Skipping custom build, will use Docker image."
  fi
}

# Function to create backup
create_backup() {
  log "Creating backups before deployment..."
  mkdir -p "$BACKUP_DIR"
  
  # Backup database if container is running
  if docker compose -f "$DOCKER_COMPOSE_FILE" ps 2>/dev/null | grep -q db; then
    log "Backing up database..."
    docker compose -f "$DOCKER_COMPOSE_FILE" exec -T db mysqldump -u photoprism -p"${MYSQL_PASSWORD}" photoprism > "$BACKUP_DIR/database.sql"
  else
    log "Database container not running, skipping database backup"
  fi
  
  # Backup configuration
  log "Backing up configuration..."
  cp "$ENV_FILE" "$BACKUP_DIR/.env.backup"
  cp "$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/docker-compose.backup.yml"
  
  log "Backups completed and stored in $BACKUP_DIR"
}

# Function to pull latest images
pull_images() {
  log "Pulling latest Docker images..."
  docker compose -f "$DOCKER_COMPOSE_FILE" pull
  log "Images pulled successfully."
}

# Function to update brain models
update_brain_models() {
  log "Updating brain models..."
  ./scripts/download-brains.sh
  log "Brain models updated successfully."
}

# Function to deploy application
deploy_app() {
  log "Deploying PhotoPrism production environment..."
  
  # Stop current containers if running
  if docker compose -f "$DOCKER_COMPOSE_FILE" ps 2>/dev/null | grep -q Up; then
    log "Stopping current containers..."
    docker compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
  fi
  
  # Start new containers
  log "Starting new containers..."
  docker compose -f "$DOCKER_COMPOSE_FILE" up -d
  
  # Check if containers started successfully
  if docker compose -f "$DOCKER_COMPOSE_FILE" ps 2>/dev/null | grep -q Exit; then
    log "ERROR: Some containers failed to start. Check the logs for details."
    docker compose -f "$DOCKER_COMPOSE_FILE" logs
    exit 1
  fi
  
  log "Deployment completed successfully."
}

# Function to verify deployment
verify_deployment() {
  log "Verifying deployment..."
  
  # Wait for services to initialize
  log "Waiting for services to initialize (30s)..."
  sleep 30
  
  # Check if PhotoPrism is responding
  PHOTOPRISM_URL=$(grep "PHOTOPRISM_SITE_URL" "$ENV_FILE" | cut -d '=' -f2 || echo "http://localhost:2342"))
  
  log "Testing connection to PhotoPrism at $PHOTOPRISM_URL..."
  if curl -s -o /dev/null -w "%{http_code}" "$PHOTOPRISM_URL" | grep -q "200\|302\|401"; then
    log "PhotoPrism is up and running!"
  else
    log "WARNING: PhotoPrism may not be fully initialized yet. Check the logs."
    docker compose -f "$DOCKER_COMPOSE_FILE" logs photoprism
  fi
  
  # Verify brain service
  log "Checking brain service..."
  if docker compose -f "$DOCKER_COMPOSE_FILE" ps 2>/dev/null | grep -q "brains.*Up"; then
    log "Brain service is running."
  else
    log "WARNING: Brain service may not be running. Check the logs."
    docker compose -f "$DOCKER_COMPOSE_FILE" logs brains
  fi
  
  log "Deployment verification completed."
}

# Main execution
main() {
  log "Starting PhotoPrism Ninja deployment process..."
  validate_environment
  build_application
  create_backup
  pull_images
  update_brain_models
  deploy_app
  verify_deployment
  log "Deployment process completed. Check logs for any warnings or errors."
}

main "$@"
