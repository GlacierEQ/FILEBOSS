# 📦 Installation Guide

This guide provides step-by-step instructions for installing and setting up the CaseBuilder evidence management system.

## 🔧 Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.11 or higher
- **Memory**: 512MB minimum, 2GB recommended
- **Storage**: 1GB minimum for application and logs
- **Network**: Internet connection for dependency installation

### Required Software

1. **Python 3.11+**
   ```bash
   # Check Python version
   python --version
   # Should output: Python 3.11.x or higher
   ```

2. **pip (Python package manager)**
   ```bash
   # Check pip version
   pip --version
   ```

3. **Git (for cloning repository)**
   ```bash
   # Check Git version
   git --version
   ```

## 🚀 Installation Methods

### Method 1: Standard Installation

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd casebuilder
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   python test_casebuilder_verification.py
   ```

5. **Run the Application**
   ```bash
   python main.py
   ```

### Method 2: Docker Installation

1. **Install Docker and Docker Compose**
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)
   - [Docker Compose Installation](https://docs.docker.com/compose/install/)

2. **Clone and Build**
   ```bash
   git clone <repository-url>
   cd casebuilder
   docker-compose up --build
   ```

3. **Verify Docker Installation**
   ```bash
   curl http://localhost:8000/health
   ```

### Method 3: Development Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd casebuilder
   ```

2. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

3. **Install Pre-commit Hooks** (Optional)
   ```bash
   pre-commit install
   ```

4. **Run in Development Mode**
   ```bash
   python main.py
   # Application will run with auto-reload enabled
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application Configuration
APP_NAME=CaseBuilder
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./casebuilder.db

# API Configuration
API_V1_STR=/api/v1
CORS_ORIGINS=*

# Security Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ALGORITHM=HS256
```

### Database Setup

#### SQLite (Default)
No additional setup required. Database file will be created automatically.

#### PostgreSQL (Optional)
```bash
# Install PostgreSQL driver
pip install asyncpg

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/casebuilder
```

## ✅ Verification

### 1. Health Check
```bash
curl http://localhost:8000/health
# Expected response:
# {"status":"healthy","service":"CaseBuilder","version":"0.1.0"}
```

### 2. API Documentation
Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Run Test Suite
```bash
python test_casebuilder_verification.py
# Expected: All tests passing with 100% score
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Python Version Error
```bash
# Error: Python 3.11+ required
# Solution: Install Python 3.11 or higher
pyenv install 3.11.0
pyenv global 3.11.0
```

#### 2. Permission Denied
```bash
# Error: Permission denied when creating database
# Solution: Check file permissions
chmod 755 .
mkdir -p data
chmod 755 data
```

#### 3. Port Already in Use
```bash
# Error: Port 8000 already in use
# Solution: Use different port
python main.py --port 8001
```

#### 4. Module Import Error
```bash
# Error: ModuleNotFoundError
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Docker Issues

#### 1. Docker Build Fails
```bash
# Clear Docker cache
docker system prune -a
docker-compose build --no-cache
```

#### 2. Container Won't Start
```bash
# Check logs
docker-compose logs casebuilder
```

## 🔄 Updates

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run verification tests
python test_casebuilder_verification.py

# Restart application
python main.py
```

### Docker Updates
```bash
# Pull latest images and rebuild
docker-compose pull
docker-compose up --build
```

## 📊 Performance Tuning

### Production Optimizations

1. **Use Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Database Optimization**
   ```bash
   # For PostgreSQL production use
   DATABASE_URL=postgresql+asyncpg://user:pass@host/db?pool_size=20&max_overflow=0
   ```

3. **Memory Configuration**
   ```bash
   # Set environment variables for production
   export PYTHONOPTIMIZE=1
   export PYTHONDONTWRITEBYTECODE=1
   ```

## 🔐 Security Hardening

### Production Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=false
- [ ] Configure proper CORS_ORIGINS
- [ ] Use HTTPS in production
- [ ] Set up proper firewall rules
- [ ] Enable access logging
- [ ] Regular security updates

### SSL/TLS Configuration
```bash
# Use reverse proxy (nginx/apache) for SSL termination
# Or configure uvicorn with SSL
uvicorn main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

---

**Installation complete! Your CaseBuilder system is ready for operation.**

Next: [API Documentation](api-reference.md)