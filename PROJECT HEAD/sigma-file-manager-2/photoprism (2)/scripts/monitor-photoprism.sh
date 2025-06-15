#!/bin/bash

# PhotoPrism Monitoring Script
# This script monitors PhotoPrism's health, performance, and storage usage

# Configuration
CONTAINER_NAME="photoprism"
LOG_FILE="photoprism-monitor.log"
ALERT_THRESHOLD_CPU=80        # CPU usage threshold (%)
ALERT_THRESHOLD_MEM=80       # Memory usage threshold (%)
ALERT_THRESHOLD_DISK=85      # Disk usage threshold (%)
CHECK_INTERVAL=300           # Check every 5 minutes

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check container health
check_container_health() {
    status=$(docker inspect -f '{{.State.Status}}' $CONTAINER_NAME 2>/dev/null)
    if [ "$status" != "running" ]; then
        log_message "WARNING: Container $CONTAINER_NAME is not running (Status: $status)"
        return 1
    fi
    return 0
}

# Function to check resource usage
check_resources() {
    # Get CPU usage
    cpu_usage=$(docker stats $CONTAINER_NAME --no-stream --format "{{.CPUPerc}}" | sed 's/%//')
    
    # Get memory usage
    mem_usage=$(docker stats $CONTAINER_NAME --no-stream --format "{{.MemPerc}}" | sed 's/%//')
    
    # Log resource usage
    log_message "Resource Usage - CPU: ${cpu_usage}%, Memory: ${mem_usage}%"
    
    # Check against thresholds
    if (( $(echo "$cpu_usage > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        log_message "WARNING: High CPU usage detected"
    fi
    
    if (( $(echo "$mem_usage > $ALERT_THRESHOLD_MEM" | bc -l) )); then
        log_message "WARNING: High memory usage detected"
    fi
}

# Function to check storage usage
check_storage() {
    # Get storage path from container
    storage_path=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/photoprism/storage"}}{{.Source}}{{end}}{{end}}' $CONTAINER_NAME)
    
    if [ -n "$storage_path" ]; then
        disk_usage=$(df -h "$storage_path" | awk 'NR==2 {print $5}' | sed 's/%//')
        log_message "Storage Usage: ${disk_usage}%"
        
        if [ "$disk_usage" -gt "$ALERT_THRESHOLD_DISK" ]; then
            log_message "WARNING: High disk usage detected"
        fi
    else
        log_message "ERROR: Could not determine storage path"
    fi
}

# Function to check database connectivity
check_database() {
    if docker exec $CONTAINER_NAME photoprism status >/dev/null 2>&1; then
        log_message "Database connection: OK"
    else
        log_message "WARNING: Database connection issues detected"
    fi
}

# Function to check indexing status
check_indexing_status() {
    # Get number of indexed files
    indexed_files=$(docker exec $CONTAINER_NAME photoprism index --count 2>/dev/null)
    log_message "Indexed files: $indexed_files"
}

# Function to perform maintenance checks
check_maintenance() {
    # Check for duplicate files
    duplicates=$(docker exec $CONTAINER_NAME photoprism duplicates --count 2>/dev/null)
    log_message "Duplicate files found: $duplicates"
    
    # Check for failed imports
    failed_imports=$(docker exec $CONTAINER_NAME photoprism import --count-failed 2>/dev/null)
    if [ "$failed_imports" -gt 0 ]; then
        log_message "WARNING: $failed_imports failed imports detected"
    fi
}

# Main monitoring loop
log_message "Starting PhotoPrism monitoring"

while true; do
    # Perform all checks
    check_container_health
    if [ $? -eq 0 ]; then
        check_resources
        check_storage
        check_database
        check_indexing_status
        check_maintenance
        log_message "-----------------------------------"
    fi
    
    # Wait for next check interval
    sleep $CHECK_INTERVAL
done
