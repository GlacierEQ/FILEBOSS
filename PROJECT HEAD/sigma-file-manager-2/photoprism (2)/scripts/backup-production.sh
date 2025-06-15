#!/bin/bash
set -e

# PhotoPrism Production Backup Script
# -----------------------------------
# This script creates comprehensive backups of your PhotoPrism installation
# including database, configuration, thumbnails, and user data.

# Default configuration
DOCKER_COMPOSE_FILE="docker/docker-compose.prod.yml"
ENV_FILE="docker/.env.prod"
BACKUP_ROOT="backups"
BACKUP_DIR="$BACKUP_ROOT/$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS=30
S3_BACKUP_ENABLED=${S3_BACKUP_ENABLED:-false}
S3_BUCKET=${S3_BUCKET:-""}
S3_PREFIX=${S3_PREFIX:-"photoprism-backups"}
LOG_FILE="backup_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to load environment variables
load_env() {
  if [ -f "$ENV_FILE" ]; then
    log "Loading environment variables from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
  else
    log "WARNING: Environment file $ENV_FILE not found. Using default values."
  fi
}

# Function to create backup directories
create_backup_dirs() {
  log "Creating backup directory structure..."
  mkdir -p "$BACKUP_DIR/database"
  mkdir -p "$BACKUP_DIR/config"
  mkdir -p "$BACKUP_DIR/storage"
}

# Function to backup database
backup_database() {
  log "Backing up database..."
  
  if ! docker compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q db; then
    log "WARNING: Database container not running, skipping database backup"
    return
  fi
  
  # Get database password from environment
  DB_PASSWORD=${MYSQL_PASSWORD:-photoprism}
  
  # Create database dump
  log "Creating SQL dump..."
  docker compose -f "$DOCKER_COMPOSE_FILE" exec -T db \
    mysqldump -u photoprism -p"$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    photoprism > "$BACKUP_DIR/database/photoprism.sql"
    
  # Compress the SQL dump
  log "Compressing SQL dump..."
  gzip -9 "$BACKUP_DIR/database/photoprism.sql"
  
  log "Database backup completed."
}

# Function to backup configuration
backup_config() {
  log "Backing up configuration..."
  
  # Copy environment file
  if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$BACKUP_DIR/config/"
  fi
  
  # Copy docker-compose file
  if [ -f "$DOCKER_COMPOSE_FILE" ]; then
    cp "$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/config/"
  fi
  
  # Export container configurations
  if docker compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q photoprism; then
    docker compose -f "$DOCKER_COMPOSE_FILE" config > "$BACKUP_DIR/config/docker-compose-resolved.yml"
  fi
  
  log "Configuration backup completed."
}

# Function to backup data
backup_data() {
  log "Backing up storage data..."
  
  # Check if storage path exists
  STORAGE_PATH=${PHOTOPRISM_STORAGE_PATH:-./storage}
  if [ ! -d "$STORAGE_PATH" ]; then
    log "WARNING: Storage path $STORAGE_PATH not found. Skipping storage backup."
    return
  fi

  # Backup thumbnails (can be recreated but saving time)
  log "Backing up thumbnails..."
  if [ -d "$STORAGE_PATH/cache/thumbnails" ]; then
    rsync -a --info=progress2 "$STORAGE_PATH/cache/thumbnails" "$BACKUP_DIR/storage/"
  fi
  
  # Backup index data
  log "Backing up index data..."
  if [ -d "$STORAGE_PATH/index" ]; then
    rsync -a --info=progress2 "$STORAGE_PATH/index" "$BACKUP_DIR/storage/"
  fi
  
  # Backup sidecar files
  log "Backing up sidecar files..."
  if [ -d "$STORAGE_PATH/sidecar" ]; then
    rsync -a --info=progress2 "$STORAGE_PATH/sidecar" "$BACKUP_DIR/storage/"
  fi

  # Backup brain data
  log "Backing up brain data..."
  if [ -d "$STORAGE_PATH/brains" ]; then
    rsync -a --info=progress2 "$STORAGE_PATH/brains" "$BACKUP_DIR/storage/"
  fi
  
  log "Storage data backup completed."
}

# Function to create compressed archive
create_archive() {
  log "Creating compressed archive of backup..."
  
  # Create tarball of the backup directory
  tar -czf "$BACKUP_ROOT/photoprism-backup-$(date +%Y%m%d_%H%M%S).tar.gz" -C "$BACKUP_ROOT" "$(basename "$BACKUP_DIR")"
  
  log "Compressed archive created: $BACKUP_ROOT/photoprism-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
}

# Function to upload backup to S3 (if configured)
upload_to_s3() {
  if [ "$S3_BACKUP_ENABLED" = "true" ] && [ ! -z "$S3_BUCKET" ]; then
    log "Uploading backup to S3 bucket: $S3_BUCKET"
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
      log "ERROR: AWS CLI not found. Please install the AWS CLI to use S3 backups."
      return 1
    fi
    
    # Upload the compressed archive
    aws s3 cp "$BACKUP_ROOT/photoprism-backup-$(date +%Y%m%d_%H%M%S).tar.gz" "s3://$S3_BUCKET/$S3_PREFIX/"
    
    log "Upload to S3 completed."
  else
    log "S3 backup not enabled or configured. Skipping upload."
  fi
}

# Function to clean up old backups
cleanup_old_backups() {
  log "Cleaning up backups older than $RETENTION_DAYS days..."
  
  # Remove old local backups
  find "$BACKUP_ROOT" -type f -name "photoprism-backup-*.tar.gz" -mtime +$RETENTION_DAYS -exec rm {} \;
  
  # Clean up old backup directories
  find "$BACKUP_ROOT" -type d -path "$BACKUP_ROOT/2*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
  
  # Clean up S3 backups if enabled
  if [ "$S3_BACKUP_ENABLED" = "true" ] && [ ! -z "$S3_BUCKET" ]; then
    # Calculate date for retention period
    RETENTION_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)
    
    # List and delete old backups from S3
    aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" | while read -r line; do
      # Extract date from filename
      BACKUP_DATE=$(echo "$line" | grep -o "[0-9]\{8\}_[0-9]\{6\}" | cut -d_ -f1)
      
      # Check if backup is older than retention period
      if [[ "$BACKUP_DATE" < "$RETENTION_DATE" ]]; then
        BACKUP_FILE=$(echo "$line" | awk '{print $4}')
        aws s3 rm "s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_FILE"
        log "Removed old S3 backup: $BACKUP_FILE"
      fi
    done
  fi
  
  log "Cleanup completed."
}

# Main execution
main() {
  log "Starting PhotoPrism production backup..."
  
  load_env
  create_backup_dirs
  backup_database
  backup_config
  backup_data
  create_archive
  upload_to_s3
  cleanup_old_backups
  
  log "Backup process completed successfully."
}

# Run the backup process
main "$@"
