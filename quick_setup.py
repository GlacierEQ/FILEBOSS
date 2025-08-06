#!/usr/bin/env python3
"""
FILEBOSS Quick Setup Script
==========================

Minimal setup script to get FILEBOSS running quickly with all core functions.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and handle errors gracefully."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def main():
    """Quick setup for FILEBOSS."""
    project_root = Path(__file__).parent
    print("🚀 FILEBOSS Quick Setup Starting...")
    
    # 1. Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", cwd=project_root):
        print("⚠️ Some dependencies may have failed to install")
    
    # 2. Create .env file if it doesn't exist
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    if not env_file.exists() and env_example.exists():
        print("\n📝 Creating .env file...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created from template")
    
    # 3. Create necessary directories
    print("\n📁 Creating directories...")
    directories = ['uploads', 'logs', 'data']
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    # 4. Check Docker availability
    print("\n🐳 Checking Docker...")
    if run_command("docker --version", check=False):
        print("✅ Docker is available")
        
        # Start services with Docker
        print("\n🚀 Starting services with Docker...")
        if run_command("docker-compose up -d", cwd=project_root):
            print("✅ Services started successfully")
            
            # Wait a bit for services to start
            print("⏳ Waiting for services to initialize...")
            import time
            time.sleep(10)
            
            # Initialize database
            print("\n🗄️ Initializing database...")
            run_command("docker-compose exec -T app python scripts/init_db.py", 
                       cwd=project_root, check=False)
        else:
            print("⚠️ Failed to start Docker services")
    else:
        print("⚠️ Docker not available - you'll need to start services manually")
        print("   1. Start PostgreSQL and Redis")
        print("   2. Run: uvicorn casebuilder.api.app:app --reload")
    
    # 5. Run the master integration
    print("\n🧠 Running master integration...")
    if run_command(f"{sys.executable} fileboss_master_integration.py --action index", 
                   cwd=project_root, check=False):
        print("✅ Project indexed successfully")
    
    # 6. Final status
    print("\n" + "="*50)
    print("🎉 FILEBOSS Quick Setup Complete!")
    print("="*50)
    print("\n📖 Next Steps:")
    print("1. Check the services are running:")
    print("   - API: http://localhost:8000/api/docs")
    print("   - PGAdmin: http://localhost:5050")
    print("\n2. Review the generated files:")
    print("   - project_index.json")
    print("   - INTEGRATION_REPORT.md")
    print("   - POWERFUL_IDEAS_COMPILATION.md")
    print("\n3. For full integration, run:")
    print("   python fileboss_master_integration.py --action all")
    print("\n4. Start developing with the API documentation at:")
    print("   http://localhost:8000/api/docs")

if __name__ == '__main__':
    main()