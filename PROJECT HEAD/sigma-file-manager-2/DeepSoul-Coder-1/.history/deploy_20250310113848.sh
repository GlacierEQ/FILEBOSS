#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  DeepSeek-Coder Production Deployment ${NC}"
echo -e "${BLUE}=======================================${NC}"

# Parse command line arguments
ENVIRONMENT="production"
MODEL_SIZE="base"
GPU_DEVICES="all"
REGISTRY=""
TAG=$(date +"%Y%m%d")
QUANTIZE="none"
BUILD_ONLY=false
MONITOR=false

# Process arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --model)
            MODEL_SIZE="$2"
            shift 2
            ;;
        --gpu)
            GPU_DEVICES="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --quantize)
            QUANTIZE="$2"
            shift 2
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --monitor)
            MONITOR=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--env development|production] [--model base|large] [--gpu all|0,1] [--registry registry-url] [--tag version] [--quantize none|4bit|8bit] [--build-only] [--monitor]"
            exit 1
            ;;
    esac
done

# Set environment variables
export MODEL_SIZE=$MODEL_SIZE
export CUDA_VISIBLE_DEVICES=$GPU_DEVICES
export REGISTRY=$REGISTRY
export TAG=$TAG

# Choose appropriate docker-compose file
COMPOSE_FILE="docker-compose.yml"
if [ "$ENVIRONMENT" == "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo -e "${YELLOW}Using production configuration: ${COMPOSE_FILE}${NC}"
else
    echo -e "${YELLOW}Using development configuration: ${COMPOSE_FILE}${NC}"
fi

# Ensure critical directories exist
mkdir -p data logs models nginx/conf.d nginx/www nginx/ssl

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check for GPU support
echo -e "${BLUE}Checking for NVIDIA Docker runtime...${NC}"
if docker info 2>/dev/null | grep -q "Runtimes:.*nvidia"; then
    echo -e "${GREEN}✓ NVIDIA Docker runtime is available${NC}"
else
    echo -e "${YELLOW}Warning: NVIDIA Docker runtime not detected. GPU acceleration will not be available.${NC}"
    echo -e "${YELLOW}To enable GPU support, install nvidia-docker2 and restart Docker daemon.${NC}"
fi

# Build or pull images
if [ -n "$REGISTRY" ] && [ "$BUILD_ONLY" = false ]; then
    echo -e "${BLUE}Pulling images from registry: ${REGISTRY}${NC}"
    docker-compose -f $COMPOSE_FILE pull
else
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose -f $COMPOSE_FILE build
fi

# Apply model quantization if requested
if [ "$QUANTIZE" != "none" ] && [ "$MODEL_SIZE" != "none" ]; then
    echo -e "${BLUE}Quantizing model to ${QUANTIZE}...${NC}"
    docker-compose -f $COMPOSE_FILE run --rm deepsoul python -m scripts.quantize_model \
        --model-path "$MODEL_PATH/${MODEL_SIZE}" \
        --output-path "${MODEL_PATH}/${MODEL_SIZE}_${QUANTIZE}" \
        --method "bitsandbytes" \
        --type "$QUANTIZE"
    
    # Update MODEL_PATH to use quantized model
    export MODEL_PATH="${MODEL_PATH}/${MODEL_SIZE}_${QUANTIZE}"
    echo -e "${GREEN}✓ Model quantized and ready to use${NC}"
fi

# Exit if build-only flag was set
if [ "$BUILD_ONLY" = true ]; then
    echo -e "${GREEN}Build completed. Exiting without starting services.${NC}"
    exit 0
fi

# Start services
echo -e "${BLUE}Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# Check if services are running
echo -e "${BLUE}Checking service status...${NC}"
sleep 5
docker-compose -f $COMPOSE_FILE ps

# Start monitoring if requested
if [ "$MONITOR" = true ]; then
    echo -e "${BLUE}Starting monitoring...${NC}"
    docker-compose -f $COMPOSE_FILE logs -f
fi

echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  Deployment completed successfully    ${NC}"
echo -e "${GREEN}=======================================${NC}"

if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "API is available at: http://localhost/api/v1"
    echo -e "Kibana is available at: http://localhost/kibana"
else
    echo -e "API is available at: http://localhost:8000"
    echo -e "Kibana is available at: http://localhost:5601"
fi

echo -e "${YELLOW}To view logs:${NC} docker-compose -f ${COMPOSE_FILE} logs -f"
echo -e "${YELLOW}To stop services:${NC} docker-compose -f ${COMPOSE_FILE} down"
echo -e ""
