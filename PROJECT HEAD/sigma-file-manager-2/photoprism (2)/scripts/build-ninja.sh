#!/bin/bash
set -e

# PhotoPrism Ninja Build Script
# This script handles building PhotoPrism using the Ninja build system

# Default configuration
BUILD_TYPE=${1:-release}
OUTPUT_NAME=${2:-photoprism}
BUILD_DIR="build"
NINJA_JOBS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

# Function to log messages
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check required tools
check_tools() {
  log "Checking required tools..."
  
  # Check if Ninja is installed
  if ! command -v ninja &> /dev/null; then
    log "ERROR: Ninja build system not found. Please install it first."
    exit 1
  fi
  
  # Check if Go is installed
  if ! command -v go &> /dev/null; then
    log "ERROR: Go compiler not found. Please install Go first."
    exit 1
  fi
  
  log "All required tools are available."
}

# Function to setup build directory
setup_build_dir() {
  log "Setting up build directory..."
  mkdir -p "$BUILD_DIR"
}

# Function to configure build
configure_build() {
  log "Configuring build..."
  
  BUILD_OS=$(uname -s)
  BUILD_ARCH=$(uname -m)
  BUILD_DATE=$(date -u +%y%m%d)
  BUILD_VERSION=$(git describe --always)
  BUILD_TAG=${BUILD_DATE}-${BUILD_VERSION}
  BUILD_ID=${BUILD_TAG}-${BUILD_OS}-${BUILD_ARCH}
  
  case "$BUILD_TYPE" in
    develop)
      BUILD_TAGS="debug,develop,brains"
      BUILD_LDFLAGS="-X main.version=${BUILD_ID}-DEVELOP"
      ;;
    race)
      BUILD_TAGS="debug,brains"
      BUILD_LDFLAGS="-X main.version=${BUILD_ID}-RACE"
      ;;
    static)
      BUILD_TAGS="static,brains"
      BUILD_LDFLAGS="-s -w -X main.version=${BUILD_ID}-STATIC"
      ;;
    debug)
      BUILD_TAGS="debug,brains"
      BUILD_LDFLAGS="-s -w -X main.version=${BUILD_ID}"
      OUTPUT_NAME="${OUTPUT_NAME}-DEBUG"
      ;;
    *)
      BUILD_TAGS="brains"
      BUILD_LDFLAGS="-s -w -X main.version=${BUILD_ID}"
      ;;
  esac
  
  log "Build configuration:"
  log "  Build Type: $BUILD_TYPE"
  log "  Build Tags: $BUILD_TAGS"
  log "  Build ID: $BUILD_ID"
  log "  Output Name: $OUTPUT_NAME"
}

# Function to download AI models if needed
download_models() {
  log "Checking AI models..."
  
  # Check if models exist
  if [ ! -d "assets/facenet" ] || [ ! -d "assets/nasnet" ]; then
    log "Downloading AI models..."
    ./scripts/download-facenet.sh
    ./scripts/download-nasnet.sh
    ./scripts/download-nsfw.sh
    ./scripts/download-brains.sh
  fi
}

# Function to build the project
build_project() {
  log "Building project with Ninja..."
  
  # Create a temporary ninja build file
  cat > "$BUILD_DIR/build.ninja" <<EOF
# Generated Ninja build file for PhotoPrism
builddir = $BUILD_DIR
bin = $OUTPUT_NAME

# Rules
rule go_build
  command = go build -tags="$BUILD_TAGS" -ldflags="$BUILD_LDFLAGS" -o \$out cmd/photoprism/photoprism.go
  description = Building PhotoPrism binary

# Build targets
build \$bin: go_build
  generator = 1
EOF

  # Run ninja
  ninja -C "$BUILD_DIR" -j "$NINJA_JOBS"
  
  # Display binary size
  du -h "$BUILD_DIR/$OUTPUT_NAME"
}

# Main execution
main() {
  log "Starting PhotoPrism Ninja build process..."
  check_tools
  setup_build_dir
  configure_build
  download_models
  build_project
  log "Build process completed successfully."
}

# Run the script
main "$@"
