#!/bin/bash

# PhotoPrism Continuous Organization Script
# This script watches for new photos and organizes them using PhotoPrism's features

# Configuration
WATCH_DIR="/mnt/files_repo"              # Directory to watch for new photos
MAX_DESC_LENGTH=30                       # Maximum length for description
PHOTOPRISM_CONTAINER="photoprism"        # Docker container name
LOG_FILE="photo-organizer.log"           # Log file for operations

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to extract EXIF date and format as YYMMDD
get_date_from_exif() {
    local file="$1"
    # Try to get DateTimeOriginal from EXIF
    local date=$(exiftool -DateTimeOriginal -d "%y%m%d" "$file" 2>/dev/null)
    
    if [ -z "$date" ]; then
        # Fallback to file creation date
        date=$(stat -c %y "$file" | cut -d' ' -f1 | sed 's/-//g' | cut -c3-)
    fi
    echo "$date"
}

# Function to get description from PhotoPrism labels or EXIF keywords
get_description() {
    local file="$1"
    local desc=""
    
    # Try to get keywords from EXIF
    desc=$(exiftool -Keywords "$file" 2>/dev/null | head -n 1 | cut -d: -f2 | sed 's/^ *//' | tr ' ' '_')
    
    # If no keywords, try to get from filename (excluding date part if present)
    if [ -z "$desc" ]; then
        desc=$(basename "$file" | sed 's/^[0-9]\{6\}_\{0,1\}//' | sed 's/\.[^.]*$//')
    fi
    
    # Truncate and sanitize description
    desc=$(echo "$desc" | tr -cd '[:alnum:]_-' | cut -c1-$MAX_DESC_LENGTH)
    echo "$desc"
}

# Function to rename file using YYMMDD_Description format
rename_photo() {
    local file="$1"
    local dir=$(dirname "$file")
    local ext="${file##*.}"
    local date=$(get_date_from_exif "$file")
    local desc=$(get_description "$file")
    local new_name="${date}_${desc}"
    local counter=1
    
    # Handle filename collisions
    while [ -e "${dir}/${new_name}.${ext}" ]; do
        new_name="${date}_${desc}_${counter}"
        ((counter++))
    done
    
    # Rename the file
    mv "$file" "${dir}/${new_name}.${ext}"
    log_message "Renamed: $file -> ${dir}/${new_name}.${ext}"
}

# Function to trigger PhotoPrism index
index_photos() {
    log_message "Triggering PhotoPrism index..."
    docker exec $PHOTOPRISM_CONTAINER photoprism index
}

# Main watch loop using inotifywait
log_message "Starting photo organization watch on $WATCH_DIR"

if ! command -v inotifywait >/dev/null; then
    log_message "Error: inotifywait not found. Please install inotify-tools."
    exit 1
fi

# Watch for new files and changes
inotifywait -m -r -e create -e moved_to "$WATCH_DIR" | while read -r directory event filename; do
    file="${directory}${filename}"
    
    # Check if the file is an image
    if [[ $filename =~ \.(jpg|jpeg|png|gif|bmp|tiff|raw|cr2|nef|arw)$ ]]; then
        log_message "New image detected: $file"
        
        # Wait a moment for any file operations to complete
        sleep 1
        
        # Rename the file
        rename_photo "$file"
        
        # Trigger PhotoPrism index
        index_photos
    fi
done
