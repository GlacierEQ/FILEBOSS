#!/bin/bash
set -e

# Function to wait for a service
wait_for_service() {
  echo "Waiting for $1 to be ready..."
  until curl -s -f "$2" > /dev/null || [ $RETRY_COUNT -ge 30 ]; do
    echo "Service $1 not ready yet (retry $RETRY_COUNT)..."
    RETRY_COUNT=$((RETRY_COUNT+1))
    sleep 2
  done

  if [ $RETRY_COUNT -lt 30 ]; then
    echo "$1 is ready!"
  else
    echo "Error: $1 was not ready in time"
    exit 1
  fi
}

# Initialize counter
RETRY_COUNT=0

# If we have ElasticSearch configured, wait for it
if [ -n "$ELASTICSEARCH_HOST" ]; then
  wait_for_service "ElasticSearch" "$ELASTICSEARCH_HOST"
fi

# Create required directories
mkdir -p "$DATA_DIR" "$LOG_DIR" "$MODEL_PATH"

# Check for first run and download model if needed
MODELS_INITIALIZED="$DATA_DIR/.models_initialized"
if [ ! -f "$MODELS_INITIALIZED" ]; then
  echo "First run detected. Checking for models..."
  MODEL_SIZE=${MODEL_SIZE:-base}
  
  case $MODEL_SIZE in
    base)
      python -m scripts.download_model --model base
      ;;
    large)
      python -m scripts.download_model --model large
      ;;
    *)
      echo "Unknown model size: $MODEL_SIZE. Using base model."
      python -m scripts.download_model --model base
      ;;
  esac
  
  # Mark as initialized
  touch "$MODELS_INITIALIZED"
fi

# Initialize database if needed
python -m scripts.init_db

# Set up logging
LOG_FILE="$LOG_DIR/deepsoul-$(date +%Y-%m-%d).log"
touch "$LOG_FILE"

# Determine execution mode
if [ "$1" = "api" ]; then
  echo "Starting API server..."
  exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --log-level ${LOG_LEVEL:-info}
elif [ "$1" = "worker" ]; then
  echo "Starting background worker..."
  exec python -m workers.task_processor
elif [ "$1" = "shell" ]; then
  echo "Starting interactive shell..."
  exec python -m IPython
else
  # Default: execute the given command
  echo "Executing: $@"
  exec "$@"
fi
