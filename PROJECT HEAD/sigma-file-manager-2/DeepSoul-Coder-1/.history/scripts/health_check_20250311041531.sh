#!/bin/bash
# Health check script for DeepSeek-Coder deployment

set -e

# Configuration
API_URL=${API_URL:-"http://localhost:8000"}
API_KEY=${API_KEY:-""}
ES_URL=${ES_URL:-"http://elasticsearch:9200"}
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "===========================================" 
echo "DeepSeek-Coder Health Check"
echo "===========================================" 
echo "API URL: $API_URL"
echo "Elasticsearch URL: $ES_URL"
echo "Timestamp: $(date)"
echo "===========================================" 

# Check API health
echo -n "Checking API health... "
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "${API_URL}/health" | grep -q "200"; then
    echo -e "${GREEN}OK${NC}"
    HEALTH_DETAILS=$(curl -s "${API_URL}/health")
    echo "Health details: $HEALTH_DETAILS"
else
    echo -e "${RED}FAILED${NC}"
    echo "API health check failed"
    API_FAILED=true
fi

# Check API with a simple completion request
if [ -z "$API_FAILED" ]; then
    echo -n "Testing API completion... "
    
    HEADERS=""
    if [ ! -z "$API_KEY" ]; then
        HEADERS="-H \"Authorization: Bearer $API_KEY\""
    fi
    
    CMD="curl -s -X POST ${API_URL}/api/v1/completion -H \"Content-Type: application/json\" $HEADERS -d '{\"prompt\": \"def hello_world():\", \"max_tokens\": 10}'"
    RESPONSE=$(eval $CMD)
    
    if echo "$RESPONSE" | grep -q "choices"; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAILED${NC}"
        echo "API test failed with response: $RESPONSE"
    fi
fi

# Check Elasticsearch if URL provided
if [ "$ES_URL" != "http://elasticsearch:9200" ] || nc -z -w1 elasticsearch 9200 2>/dev/null; then
    echo -n "Checking Elasticsearch... "
    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "${ES_URL}/_cluster/health" | grep -q "200"; then
        echo -e "${GREEN}OK${NC}"
        ES_HEALTH=$(curl -s "${ES_URL}/_cluster/health")
        echo "Elasticsearch health: $ES_HEALTH"
    else
        echo -e "${RED}FAILED${NC}"
        echo "Elasticsearch health check failed"
    fi
else
    echo -e "${YELLOW}Skipping Elasticsearch check (not available)${NC}"
fi

# Check disk space
echo -n "Checking disk space... "
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
DISK_USAGE_PCT=${DISK_USAGE%\%}

if [ "$DISK_USAGE_PCT" -lt 80 ]; then
    echo -e "${GREEN}OK${NC}"
    echo "Disk usage: $DISK_USAGE"
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "Disk usage is high: $DISK_USAGE"
fi

# Check memory
echo -n "Checking memory... "
if command -v free &> /dev/null; then
    MEM_AVAIL=$(free -m | awk 'NR==2 {print $7}')
    MEM_TOTAL=$(free -m | awk 'NR==2 {print $2}')
    MEM_USAGE_PCT=$((100 - MEM_AVAIL * 100 / MEM_TOTAL))
    
    if [ "$MEM_USAGE_PCT" -lt 80 ]; then
        echo -e "${GREEN}OK${NC}"
        echo "Memory usage: ${MEM_USAGE_PCT}%"
    else
        echo -e "${YELLOW}WARNING${NC}"
        echo "Memory usage is high: ${MEM_USAGE_PCT}%"
    fi
else
    echo -e "${YELLOW}SKIPPED${NC} (free command not available)"
fi

# Check GPU if available
echo -n "Checking GPU... "
if command -v nvidia-smi &> /dev/null; then
    GPU_MEMORY=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '{print $1 "/" $2 " MB"}')
    echo -e "${GREEN}OK${NC}"
    echo "GPU memory usage: $GPU_MEMORY"
else
    echo -e "${YELLOW}SKIPPED${NC} (NVIDIA GPU not detected)"
fi

# Check model files
echo -n "Checking model files... "
MODEL_PATH=${MODEL_PATH:-"/app/models"}
if [ -d "$MODEL_PATH" ]; then
    MODEL_COUNT=$(find "$MODEL_PATH" -name "*.bin" -o -name "*.safetensors" -o -name "*.pt" | wc -l)
    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo -e "${GREEN}OK${NC}"
        echo "Found $MODEL_COUNT model files in $MODEL_PATH"
    else
        echo -e "${YELLOW}WARNING${NC}"
        echo "No model files found in $MODEL_PATH"
    fi
else
    echo -e "${YELLOW}WARNING${NC}"
    echo "Model directory $MODEL_PATH not found"
fi

# Check container resources if running in Docker/Kubernetes
echo -n "Checking container limits... "
if [ -f /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then
    CONTAINER_MEM_LIMIT=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
    CONTAINER_MEM_LIMIT_GB=$(echo "scale=1; $CONTAINER_MEM_LIMIT / 1024 / 1024 / 1024" | bc)
    
    echo -e "${GREEN}OK${NC}"
    echo "Container memory limit: ${CONTAINER_MEM_LIMIT_GB}GB"
else
    echo -e "${YELLOW}SKIPPED${NC} (not running in container or cgroups v2)"
fi

# Summary
echo ""
echo "===========================================" 
echo "Health Check Summary"
echo "===========================================" 
if [ -z "$API_FAILED" ]; then
    echo -e "API Status: ${GREEN}OK${NC}"
else
    echo -e "API Status: ${RED}FAILED${NC}"
fi
echo "Current time: $(date)"
echo "===========================================" 
