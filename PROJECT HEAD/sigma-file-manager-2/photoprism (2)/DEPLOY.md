# PhotoPrism Quick Deployment Guide

If you're experiencing issues with the automated deployment scripts, you can use these direct commands to deploy PhotoPrism.

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned

## Simple Deployment Steps

### 1. Create Environment File

```bash
cp docker/.env.example docker/.env.prod
# Edit the file if needed:
nano docker/.env.prod
```

### 2. Create Required Directories

```bash
mkdir -p storage originals import database
```

### 3. Pull Docker Images

```bash
docker compose -f docker/docker-compose.prod.yml pull
```

### 4. Start the Containers

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

### 5. Verify Deployment

```bash
docker compose -f docker/docker-compose.prod.yml ps
```

## Common Issues and Solutions

### If containers exit immediately

Check logs:

```bash
docker compose -f docker/docker-compose.prod.yml logs
```

### If database connection fails

Ensure database container is running:

```bash
docker compose -f docker/docker-compose.prod.yml restart db
docker compose -f docker/docker-compose.prod.yml restart photoprism
```

### If BRAINS service doesn't start

Check BRAINS service logs:

```bash
docker compose -f docker/docker-compose.prod.yml logs brains
```

## Stopping and Starting

### Stop all containers

```bash
docker compose -f docker/docker-compose.prod.yml down
```

### Start all containers

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

## One-Line Direct Command

If all else fails, this single command will deploy PhotoPrism fresh:

```bash
mkdir -p storage originals import database && docker compose -f docker/docker-compose.prod.yml down --remove-orphans && docker compose -f docker/docker-compose.prod.yml pull && docker compose -f docker/docker-compose.prod.yml up -d
```

After running, PhotoPrism should be available at <http://localhost:2342>
