#!/usr/bin/env python3
"""
Enhanced OpenDevin Setup Script
Configures OpenDevin with Supabase and Ollama integration for a heightened installation
"""

import os
import sys
import subprocess
import json
import toml
from pathlib import Path

class EnhancedOpenDevinSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config = self.load_warp_config()
        
    def load_warp_config(self):
        """Load the warp.toml configuration"""
        config_path = self.project_root / "warp.toml"
        if config_path.exists():
            return toml.load(config_path)
        return {}
    
    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            print("❌ Python 3.11+ is required")
            return False
            
        # Check if Docker is available
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            print("✅ Docker is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker is not available")
            return False
            
        # Check if Poetry is available
        try:
            subprocess.run(["poetry", "--version"], check=True, capture_output=True)
            print("✅ Poetry is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Poetry not found. Will use pip instead.")
            
        return True
    
    def setup_ollama(self):
        """Setup Ollama integration"""
        print("🤖 Setting up Ollama integration...")
        
        ollama_config = self.config.get('integrations', {}).get('ollama', {})
        if not ollama_config.get('enabled', False):
            print("⏭️  Ollama integration disabled in config")
            return
            
        # Check if Ollama is running
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                print("✅ Ollama is running")
                
                # Pull required models
                models = ollama_config.get('models', [])
                for model in models:
                    print(f"📦 Pulling model: {model}")
                    subprocess.run(["ollama", "pull", model], check=False)
                    
        except Exception as e:
            print(f"⚠️  Ollama not available: {e}")
            print("💡 Install Ollama from: https://ollama.ai")
    
    def setup_supabase(self):
        """Setup Supabase integration"""
        print("🗄️  Setting up Supabase integration...")
        
        supabase_config = self.config.get('integrations', {}).get('supabase', {})
        if not supabase_config.get('enabled', False):
            print("⏭️  Supabase integration disabled in config")
            return
            
        # Check for environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("💡 Set these in your environment or .env file")
        else:
            print("✅ Supabase environment variables configured")
    
    def setup_dependencies(self):
        """Install Python dependencies"""
        print("📦 Installing dependencies...")
        
        try:
            # Try Poetry first
            subprocess.run(["poetry", "install"], check=True)
            print("✅ Dependencies installed with Poetry")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to pip
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
            print("✅ Dependencies installed with pip")
    
    def create_env_file(self):
        """Create enhanced .env file"""
        print("⚙️  Creating enhanced .env file...")
        
        env_content = """
# OpenDevin Enhanced Configuration

# LLM Configuration (Ollama)
LLM_MODEL=ollama/codellama:7b-instruct
LLM_BASE_URL=http://localhost:11434
LLM_API_KEY=ollama

# Workspace Configuration
WORKSPACE_DIR=./workspace

# Supabase Configuration (set these with your actual values)
# SUPABASE_URL=your_supabase_url
# SUPABASE_ANON_KEY=your_anon_key
# SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# OpenAI Fallback (optional)
# OPENAI_API_KEY=your_openai_key

# Enhanced Features
ENABLE_HYBRID_LLM=true
ENABLE_PERSISTENT_STORAGE=true
ENABLE_REALTIME_COLLABORATION=true
DEBUG=true
"""
        
        env_path = self.project_root / ".env"
        if not env_path.exists():
            with open(env_path, "w") as f:
                f.write(env_content)
            print("✅ .env file created")
        else:
            print("⚠️  .env file already exists")
    
    def create_workspace(self):
        """Create workspace directory"""
        workspace_dir = self.project_root / "workspace"
        workspace_dir.mkdir(exist_ok=True)
        print("✅ Workspace directory created")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting Enhanced OpenDevin Setup...")
        print("=" * 50)
        
        if not self.check_prerequisites():
            print("❌ Prerequisites check failed")
            return False
            
        self.setup_dependencies()
        self.create_env_file()
        self.create_workspace()
        self.setup_ollama()
        self.setup_supabase()
        
        print("=" * 50)
        print("🎉 Enhanced OpenDevin setup complete!")
        print("")
        print("Next steps:")
        print("1. Configure your .env file with Supabase credentials")
        print("2. Ensure Ollama is running: ollama serve")
        print("3. Start OpenDevin: python -m opendevin.main")
        print("")
        print("🔗 Access OpenDevin at: http://localhost:3000")
        
        return True

if __name__ == "__main__":
    setup = EnhancedOpenDevinSetup()
    setup.run_setup()

