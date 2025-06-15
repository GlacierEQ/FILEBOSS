#!/bin/bash
# Deploy DeepSeek-Coder to Docker Swarm

set -e

# Configuration
STACK_NAME=${STACK_NAME:-"deepseek-coder"}
CONFIG_FILE=${CONFIG_FILE:-"docker-stack.yml"}
ENV_FILE=${ENV_FILE:-".env.prod"}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  DeepSeek-Coder Swarm Deployment  ${NC}"
echo -e "${BLUE}=====================================${NC}"

# Check if running in swarm mode
echo -e "${BLUE}Checking Docker Swarm status...${NC}"
if ! docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo -e "${RED}Error: Docker is not running in Swarm mode.${NC}"
    echo "Initialize Swarm with: docker swarm init"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Check if environment file exists and source it
if [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}Loading environment from $ENV_FILE...${NC}"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo -e "${YELLOW}Warning: Environment file not found: $ENV_FILE${NC}"
    echo "Using default environment variables"
fi

# Check for required environment variables
if [ -z "$API_KEYS" ]; then
    echo -e "${YELLOW}Warning: API_KEYS not set. Using default insecure key.${NC}"
    export API_KEYS="sk-default-not-secure-change-me"
fi

if [ -z "$MODEL_SIZE" ]; then
    echo -e "${YELLOW}Warning: MODEL_SIZE not set. Using default 'base' model.${NC}"
    export MODEL_SIZE="base"
fi

# Check for required Docker images
echo -e "${BLUE}Checking for DeepSeek-Coder Docker image...${NC}"
IMAGE_NAME=${REGISTRY:-"ghcr.io/deepseek-ai"}/deepseek-coder:${TAG:-"latest"}

if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo -e "${YELLOW}Warning: Image $IMAGE_NAME not found locally.${NC}"
    echo -e "It will be pulled during deployment. This may take a while for large models."
fi

# Deploy the stack
echo -e "${BLUE}Deploying DeepSeek-Coder stack...${NC}"
if docker stack deploy -c "$CONFIG_FILE" "$STACK_NAME"; then
    echo -e "${GREEN}Stack $STACK_NAME deployed successfully!${NC}"
else
    echo -e "${RED}Failed to deploy stack $STACK_NAME${NC}"
    exit 1
fi

# Check deployment status
echo -e "${BLUE}Checking service status...${NC}"
sleep 5
docker stack services "$STACK_NAME"

# Print access information
echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}  DeepSeek-Coder Deployment Complete  ${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Access your services at:"
echo -e "API: http://localhost/api/v1"
echo -e "Health check: http://localhost/health"

if [ "$ENABLE_AUTH" == "true" ]; then
    echo -e "\n${YELLOW}Authentication is enabled. Use your API key for requests.${NC}"
    echo -e "Example: curl -H \"Authorization: Bearer YOUR_API_KEY\" http://localhost/api/v1/completion"
fi

echo -e "\nTo monitor the logs:"
echo -e "  docker service logs ${STACK_NAME}_deepsoul -f"
echo ""
echo -e "To remove the stack:"
echo -e "  docker stack rm $STACK_NAME"
echo -e "${GREEN}=====================================${NC}"
