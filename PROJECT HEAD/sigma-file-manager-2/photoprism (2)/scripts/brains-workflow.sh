#!/usr/bin/env bash

# BRAINS Automated Workflow Script
# This script automates routine BRAINS operations for PhotoPrism
# Can be used in cron jobs or CI/CD pipelines

# Default settings
PHOTOPRISM_DIR="$HOME/photoprism"
CONFIG_FILE="$PHOTOPRISM_DIR/config.yml"
LOG_FILE="$PHOTOPRISM_DIR/logs/brains-workflow.log"
MODE="analyze"  # Default mode
BATCH_SIZE=100
FORCE=false
CRON=false

# Function to log messages
log_message() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --config)
      CONFIG_FILE="$2"
      shift
      shift
      ;;
    --mode)
      MODE="$2"
      shift
      shift
      ;;
    --batch)
      BATCH_SIZE="$2"
      shift
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --cron)
      CRON=true
      shift
      ;;
    --dir)
      PHOTOPRISM_DIR="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if running from cron and system load is too high
if [[ "$CRON" == "true" ]]; then
  SYSTEM_LOAD=$(uptime | awk -F'[a-z]:' '{ print $2 }' | awk -F',' '{ print $1 }' | tr -d ' ')
  MAX_LOAD=3.0
  
  if (( $(echo "$SYSTEM_LOAD > $MAX_LOAD" | bc -l) )); then
    log_message "System load too high ($SYSTEM_LOAD > $MAX_LOAD), aborting scheduled run"
    exit 0
  fi
  
  # Also check if it's outside quiet hours (1AM-5AM)
  HOUR=$(date +%H)
  if [[ $HOUR -lt 1 || $HOUR -gt 5 ]]; then
    # Only run during quiet hours for cron jobs
    log_message "Outside quiet hours (1AM-5AM), deferring scheduled run"
    exit 0
  fi
fi

log_message "Starting BRAINS workflow in $MODE mode"

# Change to PhotoPrism directory
cd "$PHOTOPRISM_DIR" || {
  log_message "Error: Cannot change to directory $PHOTOPRISM_DIR"
  exit 1
}

# Make sure BRAINS models are downloaded
if [[ "$MODE" == "analyze" || "$MODE" == "full" ]]; then
  if [[ ! -f "assets/brains/version.txt" ]]; then
    log_message "BRAINS models not found, downloading..."
    ./scripts/download-brains.sh
    
    if [[ $? -ne 0 ]]; then
      log_message "Failed to download BRAINS models, aborting"
      exit 1
    fi
  fi
fi

# Execute the requested workflow
case $MODE in
  "analyze")
    # Run BRAINS analysis on unprocessed photos
    log_message "Analyzing new photos with BRAINS"
    
    FORCE_FLAG=""
    if [[ "$FORCE" == "true" ]]; then
      FORCE_FLAG="--force"
    fi
    
    # Use the photoprism CLI to run BRAINS analysis
    ./photoprism brains analyze $FORCE_FLAG
    
    if [[ $? -ne 0 ]]; then
      log_message "Error during BRAINS analysis"
      exit 1
    fi
    ;;
    
  "curate")
    # Run collection curation based on BRAINS data
    log_message "Curating collections based on BRAINS analysis"
    
    # This would call an API endpoint or CLI command to trigger collection curation
    curl -s -X POST "http://localhost:2342/api/v1/brains/curate" \
         -H "Content-Type: application/json" \
         -d '{"refresh": true}'
    
    if [[ $? -ne 0 ]]; then
      log_message "Error during collection curation"
      exit 1
    fi
    ;;
    
  "update")
    # Update BRAINS models
    log_message "Checking for BRAINS model updates"
    ./scripts/download-brains.sh
    
    if [[ $? -ne 0 ]]; then
      log_message "Error updating BRAINS models"
      exit 1
    fi
    ;;
    
  "full")
    # Full workflow: update models, analyze photos, curate collections
    log_message "Running full BRAINS workflow"
    
    # Update models
    log_message "Step 1/3: Checking for model updates"
    ./scripts/download-brains.sh
    
    if [[ $? -ne 0 ]]; then
      log_message "Error updating BRAINS models"
      exit 1
    fi
    
    # Analyze photos
    log_message "Step 2/3: Running photo analysis"
    FORCE_FLAG=""
    if [[ "$FORCE" == "true" ]]; then
      FORCE_FLAG="--force"
    fi
    
    ./photoprism brains analyze $FORCE_FLAG
    
    if [[ $? -ne 0 ]]; then
      log_message "Error during BRAINS analysis"
      exit 1
    fi
    
    # Curate collections
    log_message "Step 3/3: Curating collections"
    curl -s -X POST "http://localhost:2342/api/v1/brains/curate" \
         -H "Content-Type: application/json" \
         -d '{"refresh": true}'
    
    if [[ $? -ne 0 ]]; then
      log_message "Error during collection curation"
      exit 1
    fi
    ;;
    
  *)
    log_message "Unknown mode: $MODE"
    exit 1
    ;;
esac

log_message "BRAINS workflow completed successfully"
exit 0
