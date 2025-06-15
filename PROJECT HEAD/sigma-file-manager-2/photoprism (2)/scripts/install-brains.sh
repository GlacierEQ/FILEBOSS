#!/usr/bin/env bash

# Automated BRAINS Installation Script
# This script installs and configures the BRAINS neural network system for PhotoPrism

set -e

# Default settings
PHOTOPRISM_PATH="${PHOTOPRISM_PATH:-$HOME/photoprism}"
CONFIG_PATH="${CONFIG_PATH:-$PHOTOPRISM_PATH/config}"
VERBOSE=false
FORCE=false
NO_DOWNLOAD=false
DOCKER=false

# Display script usage information
show_usage() {
  echo "PhotoPrism BRAINS Installation Script"
  echo ""
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --path <path>        Path to PhotoPrism installation (default: $PHOTOPRISM_PATH)"
  echo "  --config <path>      Path to config directory (default: $CONFIG_PATH)"
  echo "  --force              Force reinstallation even if already installed"
  echo "  --no-download        Skip model download (use existing models)"
  echo "  --docker             Configure for Docker deployment"
  echo "  --verbose            Show detailed output"
  echo "  --help               Show this help information"
  echo ""
}

# Process command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --path)
      PHOTOPRISM_PATH="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --no-download)
      NO_DOWNLOAD=true
      shift
      ;;
    --docker)
      DOCKER=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      show_usage
      exit 0
      ;;
    *)
      echo "Error: Unknown option $1"
      show_usage
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

warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Check if BRAINS is already installed and configured
is_brains_installed() {
  if [[ -f "$PHOTOPRISM_PATH/assets/brains/version.txt" ]]; then
    if [[ "$FORCE" != "true" ]]; then
      status "BRAINS is already installed. Use --force to reinstall."
      return 0
    fi
  fi
  return 1
}

# Check system requirements for BRAINS
check_requirements() {
  status "Checking system requirements for BRAINS..."
  
  # Check for PhotoPrism installation
  if [[ ! -d "$PHOTOPRISM_PATH" ]]; then
    error "PhotoPrism installation not found at $PHOTOPRISM_PATH"
    exit 1
  fi
  
  # If not using Docker, check for TensorFlow dependencies
  if [[ "$DOCKER" != "true" ]]; then
    # Check for TensorFlow
    if ! command -v python3 &>/dev/null || ! python3 -c "import tensorflow" &>/dev/null; then
      warning "TensorFlow not found. Installing dependencies..."
      
      # Try to determine the OS and install accordingly
      if command -v apt-get &>/dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y python3-pip libopenblas-dev
        sudo pip3 install tensorflow
      elif command -v yum &>/dev/null; then
        # CentOS/RHEL
        sudo yum install -y python3-pip openblas-devel
        sudo pip3 install tensorflow
      elif command -v brew &>/dev/null; then
        # macOS with Homebrew
        brew install python3 openblas
        pip3 install tensorflow
      else
        error "Unsupported OS. Please install TensorFlow manually."
        exit 1
      fi
    fi
  fi
  
  status "System requirements check completed."
}

# Create necessary directories for BRAINS
create_directories() {
  status "Creating directories for BRAINS..."
  
  mkdir -p "$PHOTOPRISM_PATH/assets/brains"
  mkdir -p "$PHOTOPRISM_PATH/assets/brains/object"
  mkdir -p "$PHOTOPRISM_PATH/assets/brains/aesthetic"
  mkdir -p "$PHOTOPRISM_PATH/assets/brains/scene"
  
  # Create cache directory
  mkdir -p "$PHOTOPRISM_PATH/cache/brains"
  
  status "Directories created successfully."
}

# Download BRAINS models
download_models() {
  if [[ "$NO_DOWNLOAD" == "true" ]]; then
    status "Skipping model download as requested."
    return
  fi
  
  status "Downloading BRAINS models..."
  
  # Use the built-in download script
  DOWNLOAD_SCRIPT="$PHOTOPRISM_PATH/scripts/download-brains.sh"
  
  if [[ ! -f "$DOWNLOAD_SCRIPT" ]]; then
    warning "Download script not found. Creating it..."
    
    # Create download script if not exists
    cat > "$DOWNLOAD_SCRIPT" << 'EOF'
#!/usr/bin/env bash

TODAY=$(date -u +%Y%m%d)

MODEL_NAME="BRAINS"
MODEL_URL="https://dl.photoprism.app/tensorflow/brains.zip?$TODAY"
MODEL_PATH="assets/brains"
MODEL_ZIP="/tmp/photoprism/brains.zip"
MODEL_HASH="af5e6a2e7c791e52e2a336173e425e7b605a5d1x  $MODEL_ZIP"
MODEL_VERSION="$MODEL_PATH/version.txt"
MODEL_BACKUP="storage/backup/brains-$TODAY"

echo "Installing $MODEL_NAME model for TensorFlow..."

# Create directories and check for success
mkdir -p /tmp/photoprism || { echo "Failed to create /tmp/photoprism"; exit 1; }
mkdir -p storage/backup || { echo "Failed to create storage/backup"; exit 1; }

# Check for update
if [[ -f ${MODEL_ZIP} ]] && [[ $(sha1sum ${MODEL_ZIP}) == "${MODEL_HASH}" ]]; then
  if [[ -f ${MODEL_VERSION} ]]; then
    echo "Already up to date."
    exit
  fi
else
  # Download model
  echo "Downloading latest BRAINS model from $MODEL_URL..."
  wget --inet4-only -c "${MODEL_URL}" -O ${MODEL_ZIP}

  TMP_HASH=$(sha1sum ${MODEL_ZIP})

  echo "${TMP_HASH}"
fi

# Create backup
if [[ -e ${MODEL_PATH} ]]; then
  echo "Creating backup of existing directory: $MODEL_BACKUP"
  rm -rf "${MODEL_BACKUP}"
  mv ${MODEL_PATH} "${MODEL_BACKUP}"
fi

# Unzip model
unzip ${MODEL_ZIP} -d assets
echo "$MODEL_NAME $TODAY $MODEL_HASH" > ${MODEL_VERSION}

# Create subdirectories for different model types
mkdir -p ${MODEL_PATH}/object
mkdir -p ${MODEL_PATH}/aesthetic
mkdir -p ${MODEL_PATH}/scene

echo "Latest $MODEL_NAME neural network models installed."
echo "BRAINS is now ready to enhance your photo analysis!"
EOF
    
    chmod +x "$DOWNLOAD_SCRIPT"
  fi
  
  # Run the download script
  (cd "$PHOTOPRISM_PATH" && bash "$DOWNLOAD_SCRIPT")
  
  status "BRAINS models downloaded successfully."
}

# Configure PhotoPrism for BRAINS
configure_brains() {
  status "Configuring PhotoPrism for BRAINS..."
  
  local CONFIG_FILE="$CONFIG_PATH/options.yml"
  
  # Create config directory if it doesn't exist
  mkdir -p "$CONFIG_PATH"
  
  if [[ ! -f "$CONFIG_FILE" ]]; then
    # Create new config file
    cat > "$CONFIG_FILE" << EOF
# PhotoPrism Configuration with BRAINS
Experimental: true
Brains: true

# BRAINS capabilities
BrainsCapabilities:
  object_detection: true
  aesthetic_scoring: true
  scene_understanding: true
EOF
  else
    # Update existing config file
    if grep -q "Brains:" "$CONFIG_FILE"; then
      # Update existing BRAINS settings
      sed -i -e 's/Experimental:.*/Experimental: true/' \
             -e 's/Brains:.*/Brains: true/' "$CONFIG_FILE"
    else
      # Add BRAINS settings to existing file
      cat >> "$CONFIG_FILE" << EOF

# BRAINS Configuration
Experimental: true
Brains: true

# BRAINS capabilities
BrainsCapabilities:
  object_detection: true
  aesthetic_scoring: true
  scene_understanding: true
EOF
    fi
  fi
  
  status "PhotoPrism configured for BRAINS."
}

# Configure Docker environment
configure_docker() {
  if [[ "$DOCKER" != "true" ]]; then
    return
  fi
  
  status "Configuring Docker environment for BRAINS..."
  
  local COMPOSE_FILE="$PHOTOPRISM_PATH/docker-compose.yml"
  
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    warning "Docker Compose file not found at $COMPOSE_FILE"
    return
  }
  
  # Create a backup of the original file
  cp "$COMPOSE_FILE" "$COMPOSE_FILE.backup-$(date +%Y%m%d%H%M%S)"
  
  # Add BRAINS environment variables to Docker Compose
  if grep -q "PHOTOPRISM_BRAINS:" "$COMPOSE_FILE"; then
    # Update existing BRAINS settings
    sed -i -e 's/PHOTOPRISM_EXPERIMENTAL:.*/PHOTOPRISM_EXPERIMENTAL: "true"/' \
           -e 's/PHOTOPRISM_BRAINS:.*/PHOTOPRISM_BRAINS: "true"/' \
           -e 's/PHOTOPRISM_BRAINS_OBJECT_DETECTION:.*/PHOTOPRISM_BRAINS_OBJECT_DETECTION: "true"/' \
           -e 's/PHOTOPRISM_BRAINS_AESTHETIC_SCORING:.*/PHOTOPRISM_BRAINS_AESTHETIC_SCORING: "true"/' \
           -e 's/PHOTOPRISM_BRAINS_SCENE_UNDERSTANDING:.*/PHOTOPRISM_BRAINS_SCENE_UNDERSTANDING: "true"/' "$COMPOSE_FILE"
  else
    # Look for environment section and add BRAINS variables
    awk -i inplace '
      /environment:/ {
        print;
        print "      # BRAINS configuration";
        print "      PHOTOPRISM_EXPERIMENTAL: \"true\"";
        print "      PHOTOPRISM_BRAINS: \"true\"";
        print "      PHOTOPRISM_BRAINS_OBJECT_DETECTION: \"true\"";
        print "      PHOTOPRISM_BRAINS_AESTHETIC_SCORING: \"true\"";
        print "      PHOTOPRISM_BRAINS_SCENE_UNDERSTANDING: \"true\"";
        next;
      }
      { print }
    ' "$COMPOSE_FILE"
  fi
  
  # Add volume for BRAINS models if not exists
  if ! grep -q "./brains-models:/photoprism/assets/brains" "$COMPOSE_FILE"; then
    awk -i inplace '
      /volumes:/ {
        print;
        print "      # Volume for BRAINS models";
        print "      - \"./brains-models:/photoprism/assets/brains\"";
        next;
      }
      { print }
    ' "$COMPOSE_FILE"
  fi
  
  status "Docker environment configured for BRAINS."
}

# Setup automatic maintenance tasks
setup_automation() {
  status "Setting up automated maintenance for BRAINS..."
  
  # Create cron job for automatic analysis (but don't enable it automatically)
  local CRON_FILE="$PHOTOPRISM_PATH/scripts/brains-cron.sh"
  
  cat > "$CRON_FILE" << 'EOF'
#!/usr/bin/env bash

# BRAINS Cron Helper Script
# To set up cron jobs, run:
# crontab -e
#
# And add lines like:
# 0 3 * * * /path/to/photoprism/scripts/brains-cron.sh analyze
# 0 4 * * 0 /path/to/photoprism/scripts/brains-cron.sh update

PHOTOPRISM_PATH="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$PHOTOPRISM_PATH" || exit 1

MODE="${1:-analyze}"

case "$MODE" in
  analyze)
    ./photoprism brains analyze
    ;;
  update)
    ./scripts/download-brains.sh
    ;;
  curate)
    # Make API call to curate collections
    curl -s -X POST "http://localhost:2342/api/v1/brains/curate" \
      -H "Content-Type: application/json" \
      -d '{"refresh": true}'
    ;;
  *)
    echo "Unknown mode: $MODE"
    echo "Usage: $0 [analyze|update|curate]"
    exit 1
    ;;
esac
EOF
  
  chmod +x "$CRON_FILE"
  
  status "Automation setup complete. To enable automatic analysis, run 'crontab -e' and add the suggested cron jobs."
  echo ""
  echo "Example cron jobs:"
  echo "# Run BRAINS analysis daily at 3 AM"
  echo "0 3 * * * $CRON_FILE analyze"
  echo ""
  echo "# Update BRAINS models weekly on Sundays at 4 AM"
  echo "0 4 * * 0 $CRON_FILE update"
  echo ""
}

# Main installation process
main() {
  echo "=========================================================="
  echo "           PhotoPrism BRAINS Installation Script          "
  echo "=========================================================="
  
  # Check if already installed
  if is_brains_installed; then
    exit 0
  fi
  
  # Check system requirements
  check_requirements
  
  # Create directories
  create_directories
  
  # Download models
  download_models
  
  # Configure PhotoPrism
  configure_brains
  
  # Docker configuration
  if [[ "$DOCKER" == "true" ]]; then
    configure_docker
  fi
  
  # Setup automation
  setup_automation
  
  echo ""
  echo "=========================================================="
  status "BRAINS installation completed successfully!"
  echo ""
  status "To start using BRAINS, restart PhotoPrism and enjoy enhanced photo analysis."
  
  if [[ "$DOCKER" == "true" ]]; then
    echo ""
    status "For Docker, restart your containers with: docker-compose down && docker-compose up -d"
  fi
  echo "=========================================================="
}

# Run main installation process
main
