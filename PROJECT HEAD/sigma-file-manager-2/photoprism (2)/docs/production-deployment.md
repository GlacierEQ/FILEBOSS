# Production Deployment Guide

This guide provides comprehensive instructions for deploying PhotoPrism in a production environment. It covers both Docker-based deployments and bare-metal installations, with a focus on security, reliability, and performance.

## Deployment Methods

### Automated Deployment

For the fastest and most reliable deployment, use our automated deployment script:

```bash
# Clone the repository if you haven't already
git clone https://github.com/photoprism/photoprism.git
cd photoprism

# Run the deployment script
./scripts/deploy-production.sh
```

The script handles:

- Environment validation
- Database backups
- Image updates
- Configuration management
- Deployment verification

### Manual Docker Deployment

1. **Prepare environment file**:

   ```bash
   cp docker/.env.example docker/.env.prod
   # Edit .env.prod with your production settings
   nano docker/.env.prod
   ```

2. **Start the production stack**:

   ```bash
   docker compose -f docker/docker-compose.prod.yml --env-file docker/.env.prod up -d
   ```

3. **Verify deployment**:

   ```bash
   docker compose -f docker/docker-compose.prod.yml ps
   docker compose -f docker/docker-compose.prod.yml logs photoprism
   ```

## Production Configuration

### Resource Allocation

Configure resource limits in your `.env.prod` file:

```ini
# PhotoPrism resource limits
PHOTOPRISM_CPU_LIMIT=4
PHOTOPRISM_MEMORY_LIMIT=4G
PHOTOPRISM_CPU_RESERVATION=1
PHOTOPRISM_MEMORY_RESERVATION=1G

# Database resource limits
DB_CPU_LIMIT=2
DB_MEMORY_LIMIT=2G
DB_BUFFER_POOL_SIZE=1G
```

### Security Configuration

For enhanced security:

```ini
# Authentication
PHOTOPRISM_ADMIN_USER=admin
PHOTOPRISM_ADMIN_PASSWORD=strong-random-password
PHOTOPRISM_AUTH_MODE=password

# Disable features not needed
PHOTOPRISM_DISABLE_SETTINGS=true  # Prevent settings changes in UI
PHOTOPRISM_READONLY=true          # Read-only mode for viewing only
PHOTOPRISM_UPLOAD_NSFW=false      # Block NSFW uploads
```

### Performance Optimization

For optimal performance:

```ini
# Worker configuration
PHOTOPRISM_WORKERS=4              # Adjust based on CPU cores
BRAINS_WORKERS=2                  # For AI processing

# Thumbnail settings
PHOTOPRISM_THUMB_SIZE=2048        # Larger thumbs, better quality
PHOTOPRISM_THUMB_LIMIT=2000       # More concurrent thumbnails
PHOTOPRISM_JPEG_QUALITY=90        # Better quality thumbnails
```

## High-Availability Setup

For mission-critical deployments, consider a high-availability setup:

1. **Database replication**:
   - Configure a primary/replica MariaDB setup
   - Use external database service with automatic backups

2. **Load balancing**:
   - Deploy multiple PhotoPrism instances
   - Use Nginx or HAProxy as load balancer
   - Share storage using NFS or other distributed storage

3. **Automated failover**:
   - Configure health checks
   - Implement automatic instance replacement
   - Use container orchestration like Kubernetes

## Monitoring & Maintenance

### Health Checks

Monitor service health using the endpoints:

- PhotoPrism: `http://[your-server]:2342/api/v1/status`
- Brains: `http://[your-server]:8000/api/v1/status`

### Regular Maintenance

Schedule these maintenance tasks:

```bash
# Weekly database optimization
docker compose -f docker-compose.prod.yml exec db mysqladmin -u root -p optimize

# Monthly full backup
./scripts/backup-production.sh

# Index optimization
docker compose -f docker-compose.prod.yml exec photoprism photoprism index --cleanup
```

### Log Management

Configure log rotation:

```bash
# In your .env.prod file
PHOTOPRISM_LOG_LEVEL=info    # Use 'debug' only when troubleshooting
```

Connect logs to a centralized logging system like ELK Stack or Graylog for better monitoring.

## SSL/TLS Configuration

For secure HTTPS access:

### Option 1: Reverse Proxy (Recommended)

Use Nginx as a reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name photos.example.com;
    
    ssl_certificate /etc/letsencrypt/live/photos.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/photos.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:2342;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Large file uploads
        client_max_body_size 500M;
    }
}
```

### Option 2: Direct SSL (Advanced)

For direct SSL termination:

```ini
# In your .env.prod file
PHOTOPRISM_DISABLE_TLS=false
PHOTOPRISM_SSL_CERT=/etc/ssl/certs/photoprism.crt
PHOTOPRISM_SSL_KEY=/etc/ssl/private/photoprism.key
```

## Upgrading

To safely upgrade your production installation:

```bash
# Pull latest code
git pull origin main

# Update Docker images
docker compose -f docker-compose.prod.yml pull

# Create backup
./scripts/backup-production.sh

# Restart services
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Update brain models
./scripts/download-brains.sh
```

## Troubleshooting

### Common Issues

1. **Database connection errors**:

   ```bash
   # Check database connectivity
   docker compose -f docker-compose.prod.yml exec db mysqladmin ping -h localhost
   ```

2. **Memory issues**:

   ```bash
   # Check memory usage
   docker stats
   
   # Increase limits in .env.prod
   # PHOTOPRISM_MEMORY_LIMIT=4G
   ```

3. **Slow performance**:

   ```bash
   # Check disk I/O
   iostat -xz 1
   
   # Consider moving to SSD or increasing workers
   ```

## Additional Resources

- [PhotoPrism Documentation](https://docs.photoprism.app/)
- [Docker Compose Reference](https://docs.docker.com/compose/reference/)
- [MariaDB Performance Tuning](https://mariadb.com/kb/en/mariadb-memory-allocation/)
