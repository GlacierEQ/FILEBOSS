#!/usr/bin/env python3
"""
CaseBuilder Instant Deployment Script
Automated deployment with multiple target options.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

class CaseBuilderDeployer:
    """Automated deployment orchestrator for CaseBuilder."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_options = {
            "1": "Local Development (Docker Compose)",
            "2": "Local Production (Systemd + Nginx)",
            "3": "Cloud - Heroku",
            "4": "Cloud - Railway",
            "5": "Cloud - Render",
            "6": "Cloud - DigitalOcean App Platform",
            "7": "VPS - Ubuntu Server",
            "8": "Kubernetes Cluster"
        }
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check system prerequisites."""
        checks = {}
        
        # Check Python version
        checks["python"] = sys.version_info >= (3, 11)
        
        # Check Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            checks["docker"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            checks["docker"] = False
        
        # Check Docker Compose
        try:
            subprocess.run(["docker-compose", "--version"], capture_output=True, check=True)
            checks["docker_compose"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            checks["docker_compose"] = False
        
        # Check Git
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            checks["git"] = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            checks["git"] = False
        
        return checks
    
    def display_menu(self):
        """Display deployment options menu."""
        print("🚀 CaseBuilder Deployment Options")
        print("=" * 50)
        for key, value in self.deployment_options.items():
            print(f"{key}. {value}")
        print("=" * 50)
    
    def deploy_local_docker(self):
        """Deploy using Docker Compose for local development."""
        print("🐳 Deploying with Docker Compose...")
        
        # Create .env file if it doesn't exist
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_content = """DEBUG=true
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./casebuilder.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
"""
            env_file.write_text(env_content)
            print("✅ Created .env file")
        
        # Start Docker Compose
        try:
            subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)
            print("✅ Docker containers started successfully!")
            print("🌐 Application: http://localhost:8000")
            print("📚 API Docs: http://localhost:8000/docs")
            print("❤️ Health Check: http://localhost:8000/health")
            
            # Run verification
            print("\n🧪 Running system verification...")
            subprocess.run([sys.executable, "test_casebuilder_verification.py"])
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
    
    def deploy_heroku(self):
        """Deploy to Heroku."""
        print("☁️ Deploying to Heroku...")
        
        # Check if Heroku CLI is installed
        try:
            subprocess.run(["heroku", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Heroku CLI not found. Install from: https://devcenter.heroku.com/articles/heroku-cli")
            return
        
        app_name = input("Enter Heroku app name (or press Enter for auto-generated): ").strip()
        
        commands = [
            ["heroku", "create"] + ([app_name] if app_name else []),
            ["heroku", "addons:create", "heroku-postgresql:mini"],
            ["heroku", "config:set", "ENVIRONMENT=production"],
            ["heroku", "config:set", "DEBUG=false"],
            ["git", "push", "heroku", "main"]
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                if "heroku create" in " ".join(cmd):
                    print(f"✅ Created Heroku app: {result.stdout.strip()}")
                else:
                    print(f"✅ Executed: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Command failed: {' '.join(cmd)}")
                print(f"Error: {e.stderr}")
                return
        
        print("🎉 Heroku deployment complete!")
    
    def deploy_railway(self):
        """Deploy to Railway."""
        print("🚂 Deploying to Railway...")
        
        # Check if Railway CLI is installed
        try:
            subprocess.run(["railway", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Railway CLI not found. Install from: https://railway.app/cli")
            return
        
        commands = [
            ["railway", "login"],
            ["railway", "init"],
            ["railway", "add", "--database", "postgresql"],
            ["railway", "deploy"]
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, check=True)
                print(f"✅ Executed: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Command failed: {' '.join(cmd)}")
                return
        
        print("🎉 Railway deployment complete!")
    
    def deploy_vps_ubuntu(self):
        """Generate VPS deployment script."""
        print("🖥️ Generating VPS deployment script...")
        
        vps_script = """#!/bin/bash
# CaseBuilder VPS Deployment Script for Ubuntu 20.04+

set -e

echo "🚀 Starting CaseBuilder VPS Deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
sudo apt install -y nginx postgresql postgresql-contrib redis-server git curl

# Create application user
sudo useradd --system --shell /bin/bash --home /opt/casebuilder casebuilder

# Clone repository
sudo -u casebuilder git clone <YOUR_REPO_URL> /opt/casebuilder/app
cd /opt/casebuilder/app

# Create virtual environment
sudo -u casebuilder python3.11 -m venv /opt/casebuilder/venv
sudo -u casebuilder /opt/casebuilder/venv/bin/pip install -r requirements.txt

# Setup PostgreSQL
sudo -u postgres createdb casebuilder
sudo -u postgres createuser casebuilder
sudo -u postgres psql -c "ALTER USER casebuilder WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE casebuilder TO casebuilder;"

# Create environment file
sudo -u casebuilder tee /opt/casebuilder/app/.env << EOF
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql+asyncpg://casebuilder:secure_password@localhost/casebuilder
CORS_ORIGINS=https://yourdomain.com
EOF

# Create systemd service
sudo tee /etc/systemd/system/casebuilder.service << EOF
[Unit]
Description=CaseBuilder API
After=network.target

[Service]
Type=exec
User=casebuilder
Group=casebuilder
WorkingDirectory=/opt/casebuilder/app
Environment=PATH=/opt/casebuilder/venv/bin
ExecStart=/opt/casebuilder/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/casebuilder << EOF
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/casebuilder /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Start services
sudo systemctl daemon-reload
sudo systemctl enable casebuilder
sudo systemctl start casebuilder

# Setup SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com

echo "🎉 CaseBuilder VPS deployment complete!"
echo "🌐 Your application is available at: https://yourdomain.com"
echo "📚 API Documentation: https://yourdomain.com/docs"
echo "❤️ Health Check: https://yourdomain.com/health"
"""
        
        script_path = self.project_root / "deploy_vps.sh"
        script_path.write_text(vps_script)
        script_path.chmod(0o755)
        
        print(f"✅ VPS deployment script created: {script_path}")
        print("📝 Edit the script to add your repository URL and domain")
        print("🚀 Run on your VPS: ./deploy_vps.sh")
    
    def create_kubernetes_manifests(self):
        """Create Kubernetes deployment manifests."""
        print("☸️ Creating Kubernetes manifests...")
        
        k8s_dir = self.project_root / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        # Deployment manifest
        deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: casebuilder
  labels:
    app: casebuilder
spec:
  replicas: 3
  selector:
    matchLabels:
      app: casebuilder
  template:
    metadata:
      labels:
        app: casebuilder
    spec:
      containers:
      - name: casebuilder
        image: casebuilder:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DEBUG
          value: "false"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: casebuilder-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: casebuilder-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: casebuilder-service
spec:
  selector:
    app: casebuilder
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: casebuilder-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: casebuilder
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"""
        
        (k8s_dir / "deployment.yaml").write_text(deployment_yaml)
        
        # Secret template
        secret_yaml = """apiVersion: v1
kind: Secret
metadata:
  name: casebuilder-secrets
type: Opaque
stringData:
  database-url: "postgresql+asyncpg://user:password@postgres:5432/casebuilder"
  secret-key: "your-secret-key-here"
"""
        
        (k8s_dir / "secrets.yaml").write_text(secret_yaml)
        
        print(f"✅ Kubernetes manifests created in: {k8s_dir}")
        print("📝 Edit secrets.yaml with your actual credentials")
        print("🚀 Deploy with: kubectl apply -f k8s/")
    
    def run(self):
        """Main deployment orchestrator."""
        print("🏛️ CaseBuilder Deployment Orchestrator")
        print("=" * 50)
        
        # Check prerequisites
        checks = self.check_prerequisites()
        print("📋 System Prerequisites:")
        for check, status in checks.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check}")
        
        if not checks["python"]:
            print("❌ Python 3.11+ required. Please upgrade Python.")
            return
        
        print()
        self.display_menu()
        
        choice = input("\nSelect deployment option (1-8): ").strip()
        
        if choice == "1":
            if not checks["docker"] or not checks["docker_compose"]:
                print("❌ Docker and Docker Compose required for this option.")
                return
            self.deploy_local_docker()
        elif choice == "2":
            self.deploy_vps_ubuntu()
        elif choice == "3":
            self.deploy_heroku()
        elif choice == "4":
            self.deploy_railway()
        elif choice == "5":
            print("🎨 Render deployment: Push to GitHub and connect at render.com")
        elif choice == "6":
            print("🌊 DigitalOcean: Push to GitHub and deploy via App Platform")
        elif choice == "7":
            self.deploy_vps_ubuntu()
        elif choice == "8":
            self.create_kubernetes_manifests()
        else:
            print("❌ Invalid option selected.")

if __name__ == "__main__":
    deployer = CaseBuilderDeployer()
    deployer.run()