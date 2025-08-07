# 🚀 Deployment Guide

Complete deployment guide for the CaseBuilder evidence management system across different environments and platforms.

## 🎯 Deployment Options

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Deployment](#production-deployment)

---

## 🏠 Local Development

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd casebuilder

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py

# Access application
open http://localhost:8000
```

### Development Configuration
```bash
# Create .env file
cat > .env << EOF
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./dev_casebuilder.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
EOF
```

---

## 🐳 Docker Deployment

### Single Container Deployment

1. **Build Docker Image**
   ```bash
   docker build -t casebuilder:latest .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name casebuilder \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     -e ENVIRONMENT=production \
     casebuilder:latest
   ```

3. **Verify Deployment**
   ```bash
   curl http://localhost:8000/health
   ```

### Docker Compose Deployment

1. **Start Services**
   ```bash
   docker-compose up -d
   ```

2. **View Logs**
   ```bash
   docker-compose logs -f casebuilder
   ```

3. **Scale Services**
   ```bash
   docker-compose up -d --scale casebuilder=3
   ```

### Production Docker Compose

```yaml
version: '3.8'

services:
  casebuilder:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/casebuilder
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: casebuilder
      POSTGRES_USER: casebuilder
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - casebuilder
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create Task Definition**
   ```json
   {
     "family": "casebuilder",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "casebuilder",
         "image": "your-account.dkr.ecr.region.amazonaws.com/casebuilder:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "ENVIRONMENT",
             "value": "production"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/casebuilder",
             "awslogs-region": "us-west-2",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

2. **Deploy with AWS CLI**
   ```bash
   # Build and push image
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-west-2.amazonaws.com
   docker build -t casebuilder .
   docker tag casebuilder:latest your-account.dkr.ecr.us-west-2.amazonaws.com/casebuilder:latest
   docker push your-account.dkr.ecr.us-west-2.amazonaws.com/casebuilder:latest

   # Create service
   aws ecs create-service \
     --cluster casebuilder-cluster \
     --service-name casebuilder-service \
     --task-definition casebuilder \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Using AWS Lambda

```python
# lambda_handler.py
from mangum import Mangum
from main import app

handler = Mangum(app)
```

### Google Cloud Platform

#### Using Cloud Run

1. **Deploy to Cloud Run**
   ```bash
   # Build and deploy
   gcloud run deploy casebuilder \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ENVIRONMENT=production
   ```

2. **Configure Custom Domain**
   ```bash
   gcloud run domain-mappings create \
     --service casebuilder \
     --domain api.yourdomain.com \
     --region us-central1
   ```

### Microsoft Azure

#### Using Container Instances

```bash
# Create resource group
az group create --name casebuilder-rg --location eastus

# Deploy container
az container create \
  --resource-group casebuilder-rg \
  --name casebuilder \
  --image your-registry.azurecr.io/casebuilder:latest \
  --dns-name-label casebuilder-api \
  --ports 8000 \
  --environment-variables ENVIRONMENT=production
```

### Heroku Deployment

1. **Create Heroku App**
   ```bash
   heroku create casebuilder-api
   ```

2. **Configure Environment**
   ```bash
   heroku config:set ENVIRONMENT=production
   heroku config:set DEBUG=false
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

4. **Scale Dynos**
   ```bash
   heroku ps:scale web=2
   ```

---

## 🏭 Production Deployment

### Infrastructure Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB SSD
- **Network**: 100 Mbps

#### Recommended Requirements
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: 1 Gbps
- **Load Balancer**: Yes
- **Database**: Dedicated PostgreSQL instance

### Production Configuration

#### Environment Variables
```bash
# Application
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/casebuilder

# Security
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Monitoring
LOG_LEVEL=info
SENTRY_DSN=https://your-sentry-dsn
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/casebuilder
upstream casebuilder {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # File upload size
    client_max_body_size 100M;

    location / {
        proxy_pass http://casebuilder;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://casebuilder/health;
        access_log off;
    }
}
```

#### Systemd Service
```ini
# /etc/systemd/system/casebuilder.service
[Unit]
Description=CaseBuilder API
After=network.target

[Service]
Type=exec
User=casebuilder
Group=casebuilder
WorkingDirectory=/opt/casebuilder
Environment=PATH=/opt/casebuilder/venv/bin
ExecStart=/opt/casebuilder/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Database Setup

#### PostgreSQL Configuration
```sql
-- Create database and user
CREATE DATABASE casebuilder;
CREATE USER casebuilder WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE casebuilder TO casebuilder;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
```

### Monitoring and Logging

#### Application Monitoring
```python
# monitoring.py
import logging
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/casebuilder/app.log'),
        logging.StreamHandler()
    ]
)
```

#### Health Checks
```bash
#!/bin/bash
# health_check.sh
curl -f http://localhost:8000/health || exit 1
```

### Backup Strategy

#### Database Backup
```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/casebuilder"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h localhost -U casebuilder casebuilder > "$BACKUP_DIR/casebuilder_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/casebuilder_$DATE.sql"

# Remove old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
```

#### File Backup
```bash
#!/bin/bash
# file_backup.sh
rsync -av --delete /opt/casebuilder/data/ /backups/casebuilder/files/
```

### Security Hardening

#### SSL/TLS Configuration
```bash
# Generate SSL certificate with Let's Encrypt
certbot --nginx -d api.yourdomain.com
```

#### Firewall Configuration
```bash
# UFW firewall rules
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # Block direct access to app
ufw enable
```

#### Application Security
```python
# security.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.yourdomain.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

### Performance Optimization

#### Application Tuning
```bash
# Run with Gunicorn
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 60 \
  --keep-alive 5
```

#### Database Connection Pooling
```python
# database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

---

## 📊 Deployment Checklist

### Pre-Deployment
- [ ] Code review completed
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Documentation updated
- [ ] Backup strategy in place

### Deployment
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Load balancer configured
- [ ] Monitoring setup
- [ ] Health checks working

### Post-Deployment
- [ ] Application accessible
- [ ] All endpoints responding
- [ ] Database connectivity verified
- [ ] File uploads working
- [ ] Monitoring alerts configured
- [ ] Backup verification

---

## 🚨 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
journalctl -u casebuilder -f

# Check configuration
python -c "from casebuilder.core.config import settings; print(settings)"
```

#### Database Connection Issues
```bash
# Test database connection
python -c "
import asyncio
from casebuilder.db.base import engine
async def test():
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print('Database OK')
asyncio.run(test())
"
```

#### High Memory Usage
```bash
# Monitor memory usage
ps aux | grep python
htop

# Optimize Gunicorn workers
gunicorn main:app -w 2 --max-requests 500
```

### Performance Issues

#### Slow Response Times
```bash
# Enable query logging
export LOG_LEVEL=debug

# Monitor with htop/top
htop

# Check database performance
EXPLAIN ANALYZE SELECT * FROM evidence;
```

#### High CPU Usage
```bash
# Profile application
python -m cProfile main.py

# Reduce worker count
gunicorn main:app -w 2
```

---

**Deployment complete! Your CaseBuilder system is production-ready.**

Next: [Development Guide](development.md)