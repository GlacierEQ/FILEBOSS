#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="/opt/deepseek-coder"
USER_GROUP="deepsoul"
SERVICE_NAME="deepseek-coder"
CREATE_USER=true
CUDA_CHECK=true
USE_SYSTEMD=true
SKIP_DEPS=false
MODEL_SIZE="base"

# Print header
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  DeepSeek-Coder Linux Installation  ${NC}"
echo -e "${BLUE}=====================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: Please run as root${NC}"
  exit 1
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dir=*)
      INSTALL_DIR="${1#*=}"
      shift
      ;;
    --user=*)
      USER_GROUP="${1#*=}"
      shift
      ;;
    --no-user)
      CREATE_USER=false
      shift
      ;;
    --no-cuda)
      CUDA_CHECK=false
      shift
      ;;
    --no-systemd)
      USE_SYSTEMD=false
      shift
      ;;
    --skip-deps)
      SKIP_DEPS=true
      shift
      ;;
    --model=*)
      MODEL_SIZE="${1#*=}"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --dir=PATH         Installation directory (default: /opt/deepseek-coder)"
      echo "  --user=NAME        User and group name (default: deepsoul)"
      echo "  --no-user          Don't create a dedicated user"
      echo "  --no-cuda          Skip CUDA checks"
      echo "  --no-systemd       Don't install systemd service"
      echo "  --skip-deps        Skip installing dependencies"
      echo "  --model=SIZE       Model size to download (base or large)"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Create user if needed
if [ "$CREATE_USER" = true ]; then
  echo -e "${BLUE}Creating user ${USER_GROUP}...${NC}"
  if id "$USER_GROUP" &>/dev/null; then
    echo "User $USER_GROUP already exists"
  else
    useradd -m -s /bin/bash "$USER_GROUP"
    echo "User $USER_GROUP created"
  fi
fi

# Create installation directory
echo -e "${BLUE}Creating installation directory ${INSTALL_DIR}...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/models"

# Install system dependencies if not skipped
if [ "$SKIP_DEPS" = false ]; then
  echo -e "${BLUE}Installing system dependencies...${NC}"
  
  # Check distribution
  if [ -f /etc/os-release ]; then
    . /etc/os-release
    case $ID in
      ubuntu|debian)
        apt-get update
        apt-get install -y python3 python3-pip python3-venv git curl wget sqlite3 nginx supervisor
        
        # Install CUDA if requested
        if [ "$CUDA_CHECK" = true ]; then
          if ! command -v nvidia-smi &> /dev/null; then
            echo -e "${YELLOW}NVIDIA GPU not detected or drivers not installed${NC}"
            echo "To install NVIDIA drivers, run: apt install nvidia-driver-XXX cuda-drivers"
          else
            echo -e "${GREEN}NVIDIA GPU detected${NC}"
            nvidia-smi
          fi
        fi
        ;;
      centos|rhel|fedora)
        yum -y update
        yum -y install python3 python3-pip git curl wget sqlite nginx supervisor
        ;;
      *)
        echo -e "${YELLOW}Unsupported distribution: $ID${NC}"
        echo "Installing only Python dependencies"
        ;;
    esac
  else
    echo -e "${YELLOW}Could not determine Linux distribution${NC}"
    echo "Installing only Python dependencies"
  fi
  
  # Install Python dependencies
  echo -e "${BLUE}Installing Python dependencies...${NC}"
  python3 -m pip install --upgrade pip setuptools wheel
  python3 -m pip install torch transformers accelerate uvicorn fastapi pydantic numpy
fi

# Copy files to installation directory
echo -e "${BLUE}Copying files to ${INSTALL_DIR}...${NC}"
cp -r . "$INSTALL_DIR/"

# Set permissions
echo -e "${BLUE}Setting permissions...${NC}"
if [ "$CREATE_USER" = true ]; then
  chown -R "$USER_GROUP:$USER_GROUP" "$INSTALL_DIR"
fi
chmod +x "$INSTALL_DIR/scripts/"*.sh
chmod +x "$INSTALL_DIR/scripts/entrypoint.sh"

# Create environment file
echo -e "${BLUE}Creating environment file...${NC}"
cat > "$INSTALL_DIR/.env" << EOL
# DeepSeek-Coder Environment Configuration

# Model Configuration
MODEL_SIZE=${MODEL_SIZE}

# Server Configuration
PORT=8000
LOG_LEVEL=INFO

# Directory Configuration
MODEL_PATH=${INSTALL_DIR}/models
DATA_DIR=${INSTALL_DIR}/data
LOG_DIR=${INSTALL_DIR}/logs

# Security Configuration
ENABLE_AUTH=false
API_KEYS=sk-change-this-key
EOL

# Install systemd service if requested
if [ "$USE_SYSTEMD" = true ]; then
  echo -e "${BLUE}Installing systemd service...${NC}"
  
  # Copy service file
  cp "$INSTALL_DIR/scripts/deepseek-coder.service" /etc/systemd/system/${SERVICE_NAME}.service
  
  # Reload systemd
  systemctl daemon-reload
  
  echo -e "${GREEN}Systemd service installed: ${SERVICE_NAME}${NC}"
  echo "To enable and start the service, run:"
  echo "  systemctl enable ${SERVICE_NAME}"
  echo "  systemctl start ${SERVICE_NAME}"
fi

# Download model if available
echo -e "${BLUE}Would you like to download the model now? (y/n)${NC}"
read -r download_model
if [[ "$download_model" =~ ^[Yy]$ ]]; then
  echo -e "${BLUE}Downloading model...${NC}"
  python3 "$INSTALL_DIR/scripts/download_model.py" --model "$MODEL_SIZE"
else
  echo -e "${YELLOW}Skipping model download.${NC}"
  echo "You can download the model later by running:"
  echo "  python3 $INSTALL_DIR/scripts/download_model.py --model $MODEL_SIZE"
fi

# Final instructions
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  DeepSeek-Coder installed successfully!  ${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Installation directory: ${BLUE}${INSTALL_DIR}${NC}"
echo -e "To start the server manually, run:"
echo -e "${BLUE}cd ${INSTALL_DIR} && python3 -m uvicorn app:app --host 0.0.0.0 --port 8000${NC}"
echo ""
if [ "$USE_SYSTEMD" = true ]; then
  echo -e "To start the server as a service:"
  echo -e "${BLUE}systemctl start ${SERVICE_NAME}${NC}"
  echo -e "To enable at boot:"
  echo -e "${BLUE}systemctl enable ${SERVICE_NAME}${NC}"
  echo ""
fi
echo -e "API will be available at: http://localhost:8000/api/v1"
echo -e "Health check: http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Set ENABLE_AUTH=true and modify API_KEYS in the .env file for production use${NC}"
