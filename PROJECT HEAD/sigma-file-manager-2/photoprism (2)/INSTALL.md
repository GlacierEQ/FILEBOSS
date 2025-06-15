# PhotoPrism Professional Installation Guide

## System Requirements

### Hardware Requirements
- CPU: Multi-core processor (recommended 4+ cores)
- RAM: Minimum 4GB (recommended 8GB+ for large libraries)
- Storage: SSD recommended for better performance
  - Separate volumes for database and image storage
  - Additional space for thumbnails and cache
- GPU: Optional, but recommended for faster image processing

### Software Prerequisites
- Docker and Docker Compose (recommended method)
- Go 1.21+ (for building from source)
- Node.js 18+ and npm (for frontend development)
- MariaDB/MySQL/PostgreSQL (database options)
- ExifTool for advanced metadata operations

## Installation Methods

### 1. Docker Installation (Recommended)

```bash
# Pull the latest images
docker compose pull

# Start the services with optimized settings for large libraries
docker compose -f compose.yaml -f compose.advanced.yaml up -d
```

Example docker-compose.advanced.yaml:
```yaml
services:
  photoprism:
    environment:
      PHOTOPRISM_WORKERS: "3"              # Concurrent background workers
      PHOTOPRISM_THUMB_LIMIT: "3000"       # On-demand thumbnail limit
      PHOTOPRISM_THUMB_SIZE: "3840"        # Maximum thumbnail size in pixels
      PHOTOPRISM_JPEG_QUALITY: "90"        # JPEG quality for thumbnails
      PHOTOPRISM_DETECT_NSFW: "true"       # Enable NSFW detection
      PHOTOPRISM_EXPERIMENTAL: "true"      # Enable experimental features
    volumes:
      - "~/Pictures:/photoprism/originals"
      - "photoprism_cache:/photoprism/cache"
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### 2. Development Setup

```bash
# Clone the repository
git clone https://github.com/photoprism/photoprism.git
cd photoprism

# Download required ML models
./scripts/download-facenet.sh
./scripts/download-nasnet.sh
./scripts/download-nsfw.sh

# Build the application
make all

# Install frontend dependencies
cd frontend
npm install
npm run build
```

## Advanced Configuration

### 1. Hierarchical Organization

Configure folder structure and organization:

```env
# Folder Structure Settings
PHOTOPRISM_ORIGINALS_PATH="/path/to/photos"
PHOTOPRISM_ORIGINALS_LIMIT=1000000        # Max number of originals
PHOTOPRISM_IMPORT_PATH="/path/to/import"
PHOTOPRISM_STORAGE_PATH="/path/to/storage"

# Organization Settings
PHOTOPRISM_DISABLE_PLACES=false           # Enable/disable place detection
PHOTOPRISM_DISABLE_CLASSIFICATION=false   # Enable/disable image classification
PHOTOPRISM_DISABLE_FACES=false           # Enable/disable face detection
```

### 2. Forensic Analysis Features

Enable advanced analysis and integrity checks:

```env
# Forensic Settings
PHOTOPRISM_DETECT_NSFW=true              # NSFW content detection
PHOTOPRISM_RAW_PRESETS=false             # Disable RAW conversion presets
PHOTOPRISM_JPEG_QUALITY=100              # Maximum JPEG quality
PHOTOPRISM_THUMB_FILTER="lanczos"        # High-quality thumbnail scaling
PHOTOPRISM_THUMB_UNCACHED=true           # Create thumbnails on-demand
```

### 3. Metadata Management

Configure metadata handling and repair:

```env
# Metadata Settings
PHOTOPRISM_EXIF_BRUTEFORCE=true          # Thorough metadata extraction
PHOTOPRISM_READ_ONLY=false               # Allow metadata modifications
PHOTOPRISM_DETECT_LOCATION=true          # Geo-location detection
```

### 4. File Organization

For automatic file organization and renaming, see the [Continuous Organization](#continuous-organization) section below.


## Performance Optimization

### 1. Database Tuning

MariaDB optimization example:

```sql
SET GLOBAL innodb_buffer_pool_size = 1073741824;  -- 1GB
SET GLOBAL innodb_log_file_size = 268435456;      -- 256MB
SET GLOBAL innodb_log_buffer_size = 67108864;     -- 64MB
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL innodb_read_io_threads = 4;
SET GLOBAL innodb_write_io_threads = 4;
```

### 2. Cache Configuration

```env
# Cache Settings
PHOTOPRISM_CACHE_PATH="/fast/ssd/cache"
PHOTOPRISM_THUMB_CACHE_QUALITY=90
PHOTOPRISM_THUMB_UNCACHED=true
PHOTOPRISM_WORKERS=3
```

## Maintenance

### 1. Backup Strategy

```bash
# Database backup
docker compose exec db mysqldump -u photoprism -p photoprism > backup/db_$(date +%Y%m%d).sql

# Configuration backup
cp docker-compose.yml backup/
cp .env backup/

# Photos backup
rsync -av --progress storage/ backup/storage/
```

### 2. Regular Maintenance Tasks

```bash
# Index and repair metadata
docker compose exec photoprism photoprism index --cleanup
docker compose exec photoprism photoprism repair

# Check for duplicates
docker compose exec photoprism photoprism duplicates

# Verify checksums
docker compose exec photoprism photoprism check
```

## Troubleshooting

### Common Issues

1. Performance Issues
   ```bash
   # Check system resources
   docker stats photoprism
   
   # Clear cache if needed
   docker compose exec photoprism photoprism cleanup
   ```

2. Metadata Issues
   ```bash
   # Repair metadata
   docker compose exec photoprism photoprism repair --all
   ```

3. Storage Issues
   ```bash
   # Check storage usage
   docker compose exec photoprism photoprism storage index
   ```

## Security Considerations

1. Network Security
   ```env
   PHOTOPRISM_SITE_URL="https://photos.example.com"
   PHOTOPRISM_SITE_HTTPS="true"
   PHOTOPRISM_SITE_SSL="true"
   ```

2. Authentication
   ```env
   PHOTOPRISM_AUTH_MODE="password"
   PHOTOPRISM_ADMIN_PASSWORD="secure-password-here"
   PHOTOPRISM_PUBLIC="false"
   ```

## Continuous Organization

PhotoPrism can be configured to automatically organize and rename your photos using the provided organization script.

### Setup Automatic Organization

1. Install required dependencies:
   ```bash
   # For Debian/Ubuntu
   sudo apt-get install inotify-tools exiftool

   # For RHEL/CentOS
   sudo yum install inotify-tools perl-Image-ExifTool
   ```

2. Make the organization script executable:
   ```bash
   chmod +x scripts/organize-photos.sh
   ```

3. Configure the script:
   Edit `scripts/organize-photos.sh` and set your preferred:
   - WATCH_DIR: Directory to monitor for new photos
   - MAX_DESC_LENGTH: Maximum length for descriptions (default: 30)
   - PHOTOPRISM_CONTAINER: Docker container name

4. Run the organization script:
   ```bash
   ./scripts/organize-photos.sh
   ```

The script will:
- Watch for new photos in the specified directory
- Automatically rename files using YYMMDD_Description format
- Handle duplicate filenames
- Extract dates from EXIF data (fallback to file creation date)
- Get descriptions from EXIF keywords or filenames
- Trigger PhotoPrism indexing after processing

### Systemd Service (Optional)

To run the organization script as a service, create `/etc/systemd/system/photoprism-organizer.service`:

```ini
[Unit]
Description=PhotoPrism Photo Organizer
After=docker.service

[Service]
ExecStart=/path/to/scripts/organize-photos.sh
Restart=always
User=your-username

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable photoprism-organizer
sudo systemctl start photoprism-organizer
```

## Additional Resources

- [Official Documentation](https://docs.photoprism.app/)
- [GitHub Repository](https://github.com/photoprism/photoprism)
- [Community Forum](https://github.com/photoprism/photoprism/discussions)
- [Docker Hub](https://hub.docker.com/r/photoprism/photoprism)
