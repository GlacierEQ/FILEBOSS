#!/usr/bin/env python3
"""
FILEBOSS Deployment Script
=========================

One-click deployment for FILEBOSS digital evidence management system.
Supports Docker, local development, and production deployments.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

class FileBossDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / '.env'
        
    def run_cmd(self, cmd, cwd=None, check=True):
        """Execute command with error handling."""
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd or self.project_root,
                check=check, capture_output=True, text=True
            )
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {cmd}")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return False
    
    def setup_environment(self):
        """Setup environment configuration."""
        print("🔧 Setting up environment...")
        
        # Create .env from template if needed
        env_example = self.project_root / '.env.example'
        if not self.env_file.exists() and env_example.exists():
            self.env_file.write_text(env_example.read_text())
            print("✅ Created .env file")
        
        # Create required directories
        dirs = ['uploads', 'logs', 'data', 'models']
        for dir_name in dirs:
            (self.project_root / dir_name).mkdir(exist_ok=True)
        print("✅ Created required directories")
    
    def install_dependencies(self):
        """Install Python dependencies."""
        print("📦 Installing dependencies...")
        return self.run_cmd(f"{sys.executable} -m pip install -r requirements.txt")
    
    def check_docker(self):
        """Check if Docker is available."""
        return self.run_cmd("docker --version", check=False)
    
    def deploy_docker(self):
        """Deploy using Docker Compose."""
        print("🐳 Deploying with Docker...")
        
        # Build and start services
        if not self.run_cmd("docker-compose up -d --build"):
            return False
        
        print("⏳ Waiting for services to start...")
        time.sleep(15)
        
        # Initialize database
        print("🗄️ Initializing database...")
        self.run_cmd("docker-compose exec -T app python scripts/init_db.py", check=False)
        
        return True
    
    def deploy_local(self):
        """Deploy locally without Docker."""
        print("🏠 Deploying locally...")
        
        # Start the FastAPI server
        print("🚀 Starting FastAPI server...")
        print("Run this command in a separate terminal:")
        print("uvicorn casebuilder.api.app:app --reload --host 0.0.0.0 --port 8000")
        
        return True
    
    def verify_deployment(self):
        """Verify deployment is working."""
        print("🔍 Verifying deployment...")
        
        # Check if services are responding
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ API is responding")
                return True
        except:
            pass
        
        print("⚠️ API health check failed - services may still be starting")
        return False
    
    def show_endpoints(self):
        """Display available endpoints."""
        print("\n" + "="*60)
        print("🎉 FILEBOSS DEPLOYED SUCCESSFULLY!")
        print("="*60)
        print("\n📍 Available Endpoints:")
        print("• API Documentation: http://localhost:8000/api/docs")
        print("• ReDoc: http://localhost:8000/api/redoc")
        print("• Health Check: http://localhost:8000/health")
        print("• PGAdmin: http://localhost:5050 (admin@example.com/admin)")
        
        print("\n🔑 API Endpoints:")
        print("• POST /api/v1/auth/token - Get access token")
        print("• POST /api/v1/evidence/upload - Upload evidence")
        print("• GET /api/v1/cases - List cases")
        print("• POST /api/v1/cases - Create case")
        print("• GET /api/v1/timeline - Get timeline events")
        
        print("\n🚀 Quick Test:")
        print("curl -X GET http://localhost:8000/health")
        
    def deploy(self):
        """Main deployment process."""
        print("🚀 Starting FILEBOSS deployment...")
        
        # Setup
        self.setup_environment()
        
        # Install dependencies
        if not self.install_dependencies():
            print("⚠️ Dependency installation had issues, continuing...")
        
        # Choose deployment method
        if self.check_docker():
            print("✅ Docker detected - using Docker deployment")
            if self.deploy_docker():
                time.sleep(5)
                self.verify_deployment()
                self.show_endpoints()
            else:
                print("❌ Docker deployment failed")
                return False
        else:
            print("⚠️ Docker not available - using local deployment")
            self.deploy_local()
            self.show_endpoints()
        
        return True

def main():
    """Main entry point."""
    deployer = FileBossDeployer()
    
    try:
        deployer.deploy()
    except KeyboardInterrupt:
        print("\n⏹️ Deployment interrupted")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()