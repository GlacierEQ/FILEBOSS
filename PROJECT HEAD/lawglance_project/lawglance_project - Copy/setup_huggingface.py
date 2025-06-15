"""
Complete setup script for Hugging Face integration.
This script will:
1. Install required Hugging Face dependencies
2. Set up the API token
3. Verify access to models
4. Create a configuration file
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Constants
CONFIG_DIR = Path.home() / ".lawglance"
CONFIG_FILE = CONFIG_DIR / "config.json"
HF_TOKEN = "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"  # Default token
REQUIRED_PACKAGES = [
    "huggingface_hub",
    "transformers",
    "torch",
    "sentence-transformers"
]

def print_step(step_num, desc):
    """Print a step in the setup process."""
    print(f"\n[STEP {step_num}] {desc}")
    print("=" * 60)

def install_dependencies():
    """Install required Hugging Face packages."""
    print_step(1, "Installing required dependencies")
    
    for package in REQUIRED_PACKAGES:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"× Failed to install {package}")
            return False
    
    return True

def setup_token(token=HF_TOKEN):
    """Set up the Hugging Face token."""
    print_step(2, "Setting up Hugging Face token")
    
    # Create config directory if it doesn't exist
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)
        print(f"Created directory: {CONFIG_DIR}")
    
    # Set environment variable for current session
    os.environ["HUGGINGFACE_API_TOKEN"] = token
    
    # Save token to config file
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing config file is corrupted. Creating new one.")
    
    config["huggingface_token"] = token
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Token saved to config file: {CONFIG_FILE}")
    
    # Try to save token to huggingface_hub's token storage
    try:
        from huggingface_hub import HfFolder
        HfFolder.save_token(token)
        print("Token saved to Hugging Face Hub folder")
    except ImportError:
        print("Warning: Could not save token to Hugging Face Hub folder (huggingface_hub not installed yet)")
    except Exception as e:
        print(f"Warning: Could not save token to Hugging Face Hub folder: {e}")
    
    return True

def verify_token_access():
    """Verify token has access to Hugging Face Hub."""
    print_step(3, "Verifying token access")
    
    try:
        from huggingface_hub import HfApi
        
        api = HfApi(token=os.environ.get("HUGGINGFACE_API_TOKEN"))
        user_info = api.whoami()
        
        print(f"✓ Token verification successful!")
        print(f"  Logged in as: {user_info['name']}")
        print(f"  Email: {user_info.get('email', 'Not available')}")
        
        # Test model access
        print("\nTesting access to models...")
        models = api.list_models(filter="allennlp/longformer-base-4096")
        if models:
            print("✓ Successfully accessed model listings")
        else:
            print("! Could access API but retrieved empty model list")
        
        return True
    
    except ImportError:
        print("× Failed to import huggingface_hub. Please run the script again.")
        return False
    except Exception as e:
        print(f"× Token verification failed: {e}")
        return False

def test_transformers():
    """Test loading a small model from Hugging Face."""
    print_step(4, "Testing transformers library")
    
    try:
        from transformers import pipeline
        
        print("Loading a small sentiment analysis model...")
        classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        
        test_text = "I really enjoyed using this legal assistant!"
        result = classifier(test_text)
        
        print(f"✓ Successfully loaded and ran inference with a transformer model")
        print(f"  Test text: '{test_text}'")
        print(f"  Result: {result}")
        
        return True
    except ImportError:
        print("× Failed to import transformers. Please run the script again.")
        return False
    except Exception as e:
        print(f"× Transformer model test failed: {e}")
        return False

def create_env_script():
    """Create a script to set environment variables."""
    print_step(5, "Creating environment setup scripts")
    
    # Windows batch script
    bat_script = CONFIG_DIR / "setup_env.bat"
    with open(bat_script, "w") as f:
        f.write(f'@echo off\nset HUGGINGFACE_API_TOKEN={HF_TOKEN}\necho Hugging Face token set for this session.\n')
    
    # Unix/Linux/Mac shell script
    sh_script = CONFIG_DIR / "setup_env.sh"
    with open(sh_script, "w") as f:
        f.write(f'#!/bin/bash\nexport HUGGINGFACE_API_TOKEN={HF_TOKEN}\necho "Hugging Face token set for this session."\n')
    
    print(f"Created batch script: {bat_script}")
    print(f"Created shell script: {sh_script}")
    print("\nTo set the token in future sessions:")
    print(f"  Windows: {bat_script}")
    print(f"  Unix/Linux/Mac: source {sh_script}")

if __name__ == "__main__":
    print("=" * 60)
    print("Hugging Face Setup for Lawglance")
    print("=" * 60)
    
    # Get token from command line if provided
    token = sys.argv[1] if len(sys.argv) > 1 else HF_TOKEN
    
    if install_dependencies() and setup_token(token) and verify_token_access() and test_transformers():
        create_env_script()
        print("\n" + "=" * 60)
        print("✓ Hugging Face setup completed successfully!")
        print("  You can now use the Lawglance system with Hugging Face models.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("× Hugging Face setup encountered issues.")
        print("  Please check the error messages above and try again.")
        print("=" * 60)
