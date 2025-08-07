#!/usr/bin/env python3
"""
CaseBuilder - INSTANT START
Just run: python START.py
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 CASEBUILDER - INSTANT START")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"   Current: {sys.version}")
        sys.exit(1)
    
    # Install requirements
    print("📦 Installing requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)
    
    # Create .env if missing
    if not Path(".env").exists():
        print("📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("""DEBUG=true
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./casebuilder.db
CORS_ORIGINS=*
""")
        print("✅ .env file created")
    
    # Start the application
    print("🚀 Starting CaseBuilder...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 CaseBuilder stopped")
    except subprocess.CalledProcessError:
        print("❌ Failed to start CaseBuilder")
        sys.exit(1)

if __name__ == "__main__":
    main()