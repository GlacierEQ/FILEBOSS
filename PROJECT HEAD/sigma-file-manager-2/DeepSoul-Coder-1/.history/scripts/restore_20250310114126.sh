#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
BACKUP_PATH=""
RESTORE_CONFIG=true
RESTORE_DATA=true
RESTORE_MODELS=false
RESTART_SERVICES=false

# Print usage information
function print_usage() {
    echo -e "Usage: $0 --backup BACKUP_PATH [options]"
    echo -e "Options:"
    echo -e "  --backup PATH     Path to backup file (.tar.gz) or directory"
    echo -e "  --config-only     Restore only configuration files"
    echo -e "  --data-only       Restore only data files"
    echo -e "  --include-models  Restore model weights too (default: skip)"
    echo -e "  --restart         Restart services after restore"
    echo -e "  --help            Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup)
            BACKUP_PATH="$2"
            shift 2
            ;;
        --config-only)
            RESTORE_CONFIG=true
            RESTORE_DATA=false
            shift
            ;;
        --data-only)
            RESTORE_CONFIG=false
            RESTORE_DATA=true
            shift
            ;;
        --include-models)
            RESTORE_MODELS=true
            shift
            ;;
        --restart)
            RESTART_SERVICES=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Check if backup path is provided
if [ -z "$BACKUP_PATH" ]; then
    echo -e "${RED}Error: Backup path is required${NC}"
    print_usage
    exit 1
fi

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  DeepSeek-Coder Restore Script      ${NC}"
echo -e "${BLUE}=====================================${NC}"

# Prepare restore directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$TEMP_DIR"' EXIT  # Cleanup on exit

# Handle compressed backup
if [[ "$BACKUP_PATH" == *.tar.gz ]]; then
    echo -e "${YELLOW}Extracting backup archive...${NC}"
    tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"
    # Find the extracted directory
    EXTRACTED_DIR=$(find "$TEMP_DIR" -type d -mindepth 1 -maxdepth 1)
    if [ -z "$EXTRACTED_DIR" ]; then
        echo -e "${RED}Error: Could not find extracted directory in backup${NC}"
        exit 1
    fi
    RESTORE_SRC="$EXTRACTED_DIR"
else
    # Use directory directly
    RESTORE_SRC="$BACKUP_PATH"
fi

echo -e "${YELLOW}Restoring from: ${RESTORE_SRC}${NC}"

# Restore configuration files
if [ "$RESTORE_CONFIG" = true ]; then
    echo -e "${BLUE}Restoring configuration files...${NC}"
    
    # Restore .env files
    find "$RESTORE_SRC" -name ".env*" -exec cp {} ./ \; 2>/dev/null || true
    
    # Restore docker-compose files
    find "$RESTORE_SRC" -name "docker-compose*.yml" -exec cp {} ./ \; 2>/dev/null || true
    
    # Restore Nginx configuration
    if [ -d "$RESTORE_SRC/nginx-conf" ]; then
        echo "Restoring Nginx configuration..."
        mkdir -p nginx/conf.d
        cp -r "$RESTORE_SRC/nginx-conf"/* nginx/conf.d/ 2>/dev/null || true
    fi
    
    # Restore Prometheus configuration
    if [ -d "$RESTORE_SRC/prometheus-conf" ]; then
        echo "Restoring Prometheus configuration..."
        mkdir -p monitoring/prometheus
        cp -r "$RESTORE_SRC/prometheus-conf"/* monitoring/prometheus/ 2>/dev/null || true
    fi
    
    # Restore Grafana configuration
    if [ -d "$RESTORE_SRC/grafana-conf" ]; then
        echo "Restoring Grafana configuration..."
        mkdir -p monitoring/grafana/provisioning
        cp -r "$RESTORE_SRC/grafana-conf"/* monitoring/grafana/provisioning/ 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Configuration files restored${NC}"
fi

# Restore data files
if [ "$RESTORE_DATA" = true ]; then
    echo -e "${BLUE}Restoring data files...${NC}"
    
    # Restore data directory
    if [ -d "$RESTORE_SRC/data" ]; then
        echo "Restoring data files..."
        mkdir -p data
        cp -r "$RESTORE_SRC/data"/* data/ 2>/dev/null || true
    fi
    
    # Restore logs (if needed)
    if [ -d "$RESTORE_SRC/logs" ]; then
        echo "Restoring logs..."
        mkdir -p logs
        cp -r "$RESTORE_SRC/logs"/* logs/ 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Data files restored${NC}"
    
    # Restore model weights if requested
    if [ "$RESTORE_MODELS" = true ] && [ -d "$RESTORE_SRC/models" ]; then
        echo -e "${BLUE}Restoring model weights (this may take a while)...${NC}"
        mkdir -p models
        cp -r "$RESTORE_SRC/models"/* models/ 2>/dev/null || true
        echo -e "${GREEN}✓ Model weights restored${NC}"
    elif [ "$RESTORE_MODELS" = true ]; then
        echo -e "${YELLOW}No model weights found in backup${NC}"
    else
        echo -e "${YELLOW}Skipping model weights restore (use --include-models to restore them)${NC}"
    fi
    
    # Restore Elasticsearch indices if available
    if [ -d "$RESTORE_SRC/elasticsearch" ] && command -v docker-compose >/dev/null 2>&1; then
        if docker-compose ps | grep -q elasticsearch; then
            echo -e "${BLUE}Restoring Elasticsearch indices...${NC}"
            
            ES_CONTAINER=$(docker-compose ps -q elasticsearch)
            if [ -n "$ES_CONTAINER" ]; then
                # Read indices from backup
                INDICES_FILE="$RESTORE_SRC/elasticsearch/indices.txt"
                if [ -f "$INDICES_FILE" ]; then
                    cat "$INDICES_FILE" | while read INDEX; do
                        if [ -n "$INDEX" ]; then
                            echo "Restoring index: $INDEX"
                            INDEX_FILE="$RESTORE_SRC/elasticsearch/${INDEX}.json"
                            if [ -f "$INDEX_FILE" ]; then
                                # Delete existing index if it exists
                                docker exec $ES_CONTAINER curl -s -X DELETE "http://localhost:9200/$INDEX" > /dev/null
                                # Create new index
                                docker exec $ES_CONTAINER curl -s -X PUT "http://localhost:9200/$INDEX" > /dev/null
                                # Import data
                                cat "$INDEX_FILE" | docker exec -i $ES_CONTAINER curl -s -X POST "http://localhost:9200/$INDEX/_bulk" -H "Content-Type: application/json" --data-binary @- > /dev/null
                            fi
                        fi
                    done
                    echo -e "${GREEN}✓ Elasticsearch indices restored${NC}"
                else
                    echo -e "${YELLOW}No Elasticsearch indices found in backup${NC}"
                fi
            fi
        fi
    fi
fi

# Restart services if requested
if [ "$RESTART_SERVICES" = true ] && command -v docker-compose >/dev/null 2>&1; then
    echo -e "${BLUE}Restarting services...${NC}"
    docker-compose down
    docker-compose up -d
    echo -e "${GREEN}✓ Services restarted${NC}"
fi

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  Restore completed successfully!    ${NC}"
echo -e "${GREEN}=====================================${NC}"
