#!/usr/bin/env bash

# CI/CD Test Script for BRAINS
# This script runs automated tests for BRAINS in a CI/CD environment

set -e

# Default settings
PHOTOPRISM_PATH="${PHOTOPRISM_PATH:-/photoprism}"
TEST_IMAGE="sample.jpg"
VERBOSE=false
EXIT_ON_ERROR=true

# Process command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      PHOTOPRISM_PATH="$2"
      shift 2
      ;;
    --test-image)
      TEST_IMAGE="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --no-exit-on-error)
      EXIT_ON_ERROR=false
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --path <path>          Path to PhotoPrism installation (default: $PHOTOPRISM_PATH)"
      echo "  --test-image <image>   Image file to use for testing (default: $TEST_IMAGE)"
      echo "  --verbose              Show detailed output"
      echo "  --no-exit-on-error     Continue tests even if some fail"
      echo "  --help                 Show this help information"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Function for verbose logging
log() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
  fi
}

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print colored status messages
status() {
  echo -e "${GREEN}[STATUS]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
  if [[ "$EXIT_ON_ERROR" == "true" ]]; then
    exit 1
  fi
}

# Check if BRAINS is properly installed
test_installation() {
  status "Testing BRAINS installation..."
  
  if [[ ! -f "$PHOTOPRISM_PATH/assets/brains/version.txt" ]]; then
    error "BRAINS models not found. Run download-brains.sh to install."
  else
    success "BRAINS models are installed."
  fi
  
  # Check directory structure
  for dir in "object" "aesthetic" "scene"; do
    if [[ ! -d "$PHOTOPRISM_PATH/assets/brains/$dir" ]]; then
      warning "Missing BRAINS directory: $dir"
    fi
  done
}

# Test image processing with BRAINS
test_image_processing() {
  status "Testing BRAINS image processing..."
  
  # Check if test image exists
  if [[ ! -f "$TEST_IMAGE" ]]; then
    warning "Test image not found: $TEST_IMAGE. Using placeholder."
    # Create a placeholder test image
    TEST_IMAGE="/tmp/brains-test.jpg"
    convert -size 640x480 xc:white "$TEST_IMAGE" || {
      error "Failed to create test image. Install ImageMagick or provide a test image."
    }
  fi
  
  # Run BRAINS analysis on the test image
  cd "$PHOTOPRISM_PATH"
  
  log "Running BRAINS analysis on $TEST_IMAGE..."
  ./photoprism brains analyze --path "$TEST_IMAGE" 2>&1 || {
    error "BRAINS analysis failed for test image."
  }
  
  success "BRAINS analysis completed successfully."
}

# Test API endpoints for BRAINS
test_api_endpoints() {
  status "Testing BRAINS API endpoints..."
  
  # Check if PhotoPrism is running
  if ! curl -s "http://localhost:2342/api/v1/status" > /dev/null; then
    warning "PhotoPrism API is not accessible. API tests skipped."
    return
  }
  
  # Test BRAINS status endpoint
  log "Testing BRAINS status API..."
  BRAINS_STATUS=$(curl -s "http://localhost:2342/api/v1/brains/status")
  
  # Check if API call was successful
  if [[ "$BRAINS_STATUS" == *"enabled"* ]]; then
    success "BRAINS status API is working."
  else
    error "BRAINS status API test failed."
  fi
  
  # Test other BRAINS endpoints if needed
}

# Run all tests
run_all_tests() {
  echo "======================================================"
  echo "           PhotoPrism BRAINS CI/CD Test Suite         "
  echo "======================================================"
  
  test_installation
  test_image_processing
  test_api_endpoints
  
  echo ""
  echo "======================================================"
  success "All BRAINS tests completed."
  echo "======================================================"
}

# Execute the test suite
run_all_tests
