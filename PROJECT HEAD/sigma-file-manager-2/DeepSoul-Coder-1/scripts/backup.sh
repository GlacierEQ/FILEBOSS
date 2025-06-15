#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
BACKUP_DIR="./backups"
BACKUP_NAME="deepseek-backup-$(date +%Y%m%d-%H%M%S)"
INCLUDE_MODELS=false
COMPRESS=true

# Print usage information
function print_usage() {
    echo -e "Usage: $0 [options]"
    echo -e "Options:"
    echo -e "  --dir DIR         Backup directory (default: ./backups)"
    echo -e "  --name NAME       Backup name (default: deepseek-backup-TIMESTAMP)"
    echo -e "  --include-models  Include model weights in backup (default: false)"
    echo -e "  --no-compress     Skip compression of backup (default: compress)"
    echo -e "  --help            Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        --include-models)
            INCLUDE_MODELS=true
            shift
            ;;
        --no-compress)
            COMPRESS=false
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

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  DeepSeek-Coder Backup Script       ${NC}"
echo -e "${BLUE}=====================================${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "$BACKUP_PATH"

echo -e "${YELLOW}Creating backup in ${BACKUP_PATH}${NC}"

# Backup configuration files
echo -e "${BLUE}Backing up configuration files...${NC}"
cp -r .env* "$BACKUP_PATH/" 2>/dev/null || true
cp -r docker-compose*.yml "$BACKUP_PATH/" 2>/dev/null || true
cp -r nginx/conf.d "$BACKUP_PATH/nginx-conf" 2>/dev/null || true
cp -r monitoring/prometheus "$BACKUP_PATH/prometheus-conf" 2>/dev/null || true
cp -r monitoring/grafana/provisioning "$BACKUP_PATH/grafana-conf" 2>/dev/null || true

# Backup data
echo -e "${BLUE}Backing up data...${NC}"
if [ -d "data" ]; then
    mkdir -p "${BACKUP_PATH}/data"
    cp -r data/* "${BACKUP_PATH}/data/" 2>/dev/null || true
fi

# Backup logs (only recent ones)
echo -e "${BLUE}Backing up recent logs...${NC}"
if [ -d "logs" ]; then
    mkdir -p "${BACKUP_PATH}/logs"
    find logs -type f -name "*.log" -mtime -7 -exec cp {} "${BACKUP_PATH}/logs/" \; 2>/dev/null || true
fi

# Backup models if requested
if [ "$INCLUDE_MODELS" = true ]; then
    echo -e "${BLUE}Backing up model weights (this may take a while)...${NC}"
    if [ -d "models" ]; then
        mkdir -p "${BACKUP_PATH}/models"
        cp -r models/* "${BACKUP_PATH}/models/" 2>/dev/null || true
    fi
else
    echo -e "${YELLOW}Skipping model weights backup (use --include-models to include them)${NC}"
fi

# Export Elasticsearch indices if available
if command -v docker-compose >/dev/null 2>&1; then
    if docker-compose ps | grep -q elasticsearch; then
        echo -e "${BLUE}Exporting Elasticsearch indices...${NC}"
        
        ES_CONTAINER=$(docker-compose ps -q elasticsearch)
        if [ -n "$ES_CONTAINER" ]; then
            mkdir -p "${BACKUP_PATH}/elasticsearch"
            
            # List and export all indices
            INDICES=$(docker exec $ES_CONTAINER curl -s -X GET "http://localhost:9200/_cat/indices?h=index")
            echo "$INDICES" > "${BACKUP_PATH}/elasticsearch/indices.txt"
            
            for INDEX in $INDICES; do
                echo "Exporting index: $INDEX"
                docker exec $ES_CONTAINER curl -s -X GET "http://localhost:9200/${INDEX}/_search?size=10000" \
                    > "${BACKUP_PATH}/elasticsearch/${INDEX}.json"
            done
        fi
    fi
fi

# Compress backup if requested
if [ "$COMPRESS" = true ]; then
    echo -e "${BLUE}Compressing backup...${NC}"
    COMPRESSED_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    tar -czf "$COMPRESSED_FILE" -C "$BACKUP_DIR" "$BACKUP_NAME"
    
    # Remove uncompressed directory
    rm -rf "$BACKUP_PATH"
    
    echo -e "${GREEN}Backup completed successfully: ${COMPRESSED_FILE}${NC}"
else
    echo -e "${GREEN}Backup completed successfully: ${BACKUP_PATH}${NC}"
fi

# Show backup size
if [ "$COMPRESS" = true ]; then
    BACKUP_SIZE=$(du -sh "$COMPRESSED_FILE" | cut -f1)
    echo -e "Backup size: ${YELLOW}${BACKUP_SIZE}${NC}"
else
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    echo -e "Backup size: ${YELLOW}${BACKUP_SIZE}${NC}"
fi

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  Backup completed successfully!     ${NC}"
echo -e "${GREEN}=====================================${NC}"

#!/bin/bash
# Backup script for DeepSeek-Coder data

set -e

# Configuration
BACKUP_DIR=${1:-"/backups"}
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_NAME="deepseek-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
MODELS_DIR=${MODELS_DIR:-"/app/models"}
DATA_DIR=${DATA_DIR:-"/app/data"}
ES_DATA_DIR=${ES_DATA_DIR:-"/backup/elasticsearch"}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Create backup directory
mkdir -p "${BACKUP_PATH}"

echo "Starting backup at $(date)"
echo "Backup path: ${BACKUP_PATH}"

# Backup model files
echo "Backing up models..."
if [ -d "${MODELS_DIR}" ]; then
  tar -czf "${BACKUP_PATH}/models.tar.gz" -C "$(dirname "${MODELS_DIR}")" "$(basename "${MODELS_DIR}")" || echo "Warning: Error backing up models"
else
  echo "Models directory not found, skipping"
fi

# Backup application data
echo "Backing up application data..."
if [ -d "${DATA_DIR}" ]; then
  tar -czf "${BACKUP_PATH}/data.tar.gz" -C "$(dirname "${DATA_DIR}")" "$(basename "${DATA_DIR}")" || echo "Warning: Error backing up data"
else
  echo "Data directory not found, skipping"
fi

# Backup Elasticsearch if available
echo "Backing up Elasticsearch data..."
if [ -d "${ES_DATA_DIR}" ]; then
  # Create Elasticsearch backup
  tar -czf "${BACKUP_PATH}/elasticsearch.tar.gz" -C "$(dirname "${ES_DATA_DIR}")" "$(basename "${ES_DATA_DIR}")" || echo "Warning: Error backing up Elasticsearch"
else
  echo "Elasticsearch data directory not found, skipping"
fi

# Create backup metadata
echo "Creating backup metadata..."
cat > "${BACKUP_PATH}/metadata.json" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "backup_name": "${BACKUP_NAME}",
  "components": {
    "models": $([ -f "${BACKUP_PATH}/models.tar.gz" ] && echo "true" || echo "false"),
    "data": $([ -f "${BACKUP_PATH}/data.tar.gz" ] && echo "true" || echo "false"),
    "elasticsearch": $([ -f "${BACKUP_PATH}/elasticsearch.tar.gz" ] && echo "true" || echo "false")
  },
  "sizes": {
    "models": $([ -f "${BACKUP_PATH}/models.tar.gz" ] && stat -c %s "${BACKUP_PATH}/models.tar.gz" || echo "0"),
    "data": $([ -f "${BACKUP_PATH}/data.tar.gz" ] && stat -c %s "${BACKUP_PATH}/data.tar.gz" || echo "0"),
    "elasticsearch": $([ -f "${BACKUP_PATH}/elasticsearch.tar.gz" ] && stat -c %s "${BACKUP_PATH}/elasticsearch.tar.gz" || echo "0")
  }
}
EOF

# Create single archive of everything
echo "Creating final archive..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}"

# Clean up temporary directory
rm -rf "${BACKUP_PATH}"

echo "Backup completed at $(date)"

# Clean up old backups
find "${BACKUP_DIR}" -name "deepseek-backup-*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "Removed backups older than ${RETENTION_DAYS} days"

echo "Backup completed successfully"
