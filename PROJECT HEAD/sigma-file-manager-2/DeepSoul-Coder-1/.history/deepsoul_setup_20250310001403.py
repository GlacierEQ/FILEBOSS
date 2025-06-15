#!/usr/bin/env python3
"""
DeepSoul Setup - Script to set up the DeepSoul environment
"""
import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("deepsoul_setup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DeepSoul-Setup")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import torch
        import transformers
        import psutil
        import watchdog
        import elasticsearch
        import fastapi
        import uvicorn
        import py3nvml
        import undetected_chromedriver
        import playwright
        import beautifulsoup4
        import pandas
        import rich
        
        logger.info("All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False

def install_dependencies():
    """Install required dependencies using pip"""
    try:
        # Install dependencies from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Install additional dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "selenium", "undetected-chromedriver", "beautifulsoup4", "pandas", "elasticsearch", "fastapi", "uvicorn", "py3nvml"])
        
        # Install playwright browsers
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        
        logger.info("All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def create_default_directories():
    """Create default directories for DeepSoul"""
    directories = [
        "knowledge_store",
        "fine_tuned_models",
        "task_checkpoints",
        "memory_dumps",
        "deepsoul_config",
        "deepsoul_config/models",
        "inference_outputs",
        "legal_data"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")

def generate_default_configs():
    """Generate default configuration files"""
    try:
        # Generate default memory configuration
        from utils.setup_memory_protection import generate_default_config as generate_memory_config
        generate_memory_config("deepsoul_config/memory_config.json")
        
        # Generate default system configuration
        default_system_config = {
            "model_name": "deepseek-ai/deepseek-coder-1.3b-instruct",
            "device": "cuda",
            "knowledge_store_path": "knowledge_store.db",
            "learning_output_dir": "fine_tuned_models",
            "task_checkpoint_dir": "task_checkpoints",
            "max_concurrent_tasks": 4,
            "auto_learning_enabled": False,
            "auto_knowledge_acquisition": False,
            "api_keys": {
                "courtlistener": "YOUR_COURTLISTENER_API_KEY",
                "memoryplugin": "YOUR_MEMORYPLUGIN_API_TOKEN",
                "2captcha": "YOUR_2CAPTCHA_API_KEY"
            },
            "aion777_enabled": False,
            "aion777_mode": False
        }
        
        with open("deepsoul_config/system_config.json", 'w') as f:
            json.dump(default_system_config, f, indent=4)
        
        logger.info("Generated default configuration files")
    except Exception as e:
        logger.error(f"Error generating default configuration files: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="DeepSoul Setup Script")
    parser.add_argument("--check", action="store_true", help="Check if dependencies are installed")
    parser.add_argument("--install", action="store_true", help="Install missing dependencies")
    parser.add_argument("--create-dirs", action="store_true", help="Create default directories")
    parser.add_argument("--generate-configs", action="store_true", help="Generate default configuration files")
    args = parser.parse_args()
    
    if args.check:
        check_dependencies()
    elif args.install:
        install_dependencies()
    elif args.create_dirs:
        create_default_directories()
    elif args.generate_configs:
        generate_default_configs()
    else:
        print("No action specified. Use --help for options.")

if __name__ == "__main__":
    main()
