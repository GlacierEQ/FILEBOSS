#!/bin/bash
# Restore script for DeepSeek-Coder data

set -e

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <backup_file> [target_dir]"
    exit 1
fi

BACKUP_FILE=$1
TARGET_DIR=${2:-"/"}
TEMP_DIR="/tmp/deepseek-restore-$(date +%s)"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting restore process at $(date)"
echo "Backup file: $BACKUP_FILE"
echo "Target directory: $TARGET_DIR"

# Create temporary directory
mkdir -p "$TEMP_DIR"
echo "Created temporary directory: $TEMP_DIR"

# Extract the main backup archive
echo "Extracting main backup archive..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Find the extracted backup directory
BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -name "deepseek-backup-*" -type d)
if [ -z "$BACKUP_DIR" ]; then
    echo "Error: Could not find backup directory in the archive"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Extracted backup directory: $BACKUP_DIR"

# Check metadata
if [ -f "$BACKUP_DIR/metadata.json" ]; then
    echo "Backup metadata:"
    cat "$BACKUP_DIR/metadata.json"
else
    echo "Warning: No metadata file found in backup"
fi

# Restore models
if [ -f "$BACKUP_DIR/models.tar.gz" ]; then
    echo "Restoring models..."
    tar -xzf "$BACKUP_DIR/models.tar.gz" -C "$TARGET_DIR"
    echo "Models restored"
else
    echo "No models backup found, skipping"
fi

# Restore application data
if [ -f "$BACKUP_DIR/data.tar.gz" ]; then
    echo "Restoring application data..."
    tar -xzf "$BACKUP_DIR/data.tar.gz" -C "$TARGET_DIR"
    echo "Application data restored"
else
    echo "No application data backup found, skipping"
fi

# Restore Elasticsearch data
if [ -f "$BACKUP_DIR/elasticsearch.tar.gz" ]; then
    echo "Restoring Elasticsearch data..."
    tar -xzf "$BACKUP_DIR/elasticsearch.tar.gz" -C "$TARGET_DIR"
    echo "Elasticsearch data restored"
else
    echo "No Elasticsearch backup found, skipping"
fi

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Restore process completed at $(date)"
echo "Remember to restart services to apply the restored data"
