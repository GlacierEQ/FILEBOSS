#!/usr/bin/env python3
"""
DeepSoul Setup Script - Install dependencies and prepare the environment
"""
import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def run_command(command, description=None):
    """Run a shell command and print its output"""
    if description:
        print(f"\n>> {description}")
    
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    
    major, minor, _ = platform.python_version_tuple()
    version_str = f"{major}.{minor}"
    
    print(f"Python version: {platform.python_version()}")
    
    if int(major) < 3 or (int(major) == 3 and int(minor) < 8):
        print("ERROR: DeepSoul requires Python 3.8 or higher")
        return False
    
    return True

def check_gpu():
    """Check for GPU availability"""
    print_header("Checking GPU Availability")
    
    has_cuda = False
    has_gpu = False
    
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if has_cuda else 0
        device_name = torch.cuda.get_device_name(0) if device_count > 0 else "None"
        
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {has_cuda}")
        print(f"GPU count: {device_count}")
        print(f"GPU device: {device_name}")
        
        has_gpu = has_cuda and device_count > 0
        
    except ImportError:
        print("PyTorch not installed. Will be installed during setup.")
    
    if not has_gpu:
        print("WARNING: No GPU detected. DeepSoul will run on CPU, which will be significantly slower.")
        print("         For optimal performance, a CUDA-compatible GPU is recommended.")
    else:
        print("GPU detected! DeepSoul will use GPU acceleration.")
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print_header("Installing Dependencies")
    
    # Core requirements
    success = run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installing core requirements"
    )
    
    if not success:
        print("WARNING: Some packages failed to install. Will continue anyway.")
    
    # Additional UI dependencies
    run_command(
        [sys.executable, "-m", "pip", "install", "rich", "gradio"],
        "Installing UI dependencies"
    )
    
    return True

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    
    dirs = [
        "deepsoul_config",
        "fine_tuned_models",
        "task_checkpoints", 
        "knowledge_store"
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

def create_config():
    """Create initial configuration file"""
    print_header("Creating Configuration")
    
    import json
    
    config = {
        "model_name": "deepseek-ai/deepseek-coder-1.3b-instruct",
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "knowledge_store_path": "knowledge_store/knowledge.db",
        "learning_output_dir": "fine_tuned_models",
        "task_checkpoint_dir": "task_checkpoints",
        "max_concurrent_tasks": 2 if torch.cuda.is_available() else 1,
        "auto_learning_enabled": False,
        "auto_knowledge_acquisition": False
    }
    
    os.makedirs("deepsoul_config", exist_ok=True)
    config_path = "deepsoul_config/system_config.json"
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Created configuration file: {config_path}")
    return True

def create_batch_file():
    """Create Windows batch file for easy launching"""
    print_header("Creating Launch Script")
    
    batch_content = """@echo off
echo Starting DeepSoul Code Intelligence System...

REM Check if the user has GPU support
where nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected. Using GPU for inference.
    python deepsoul_launch.py %*
) else (
    echo No NVIDIA GPU detected. Using CPU mode.
    python deepsoul_launch.py --cpu %*
)

pause
"""
    
    with open("run_deepsoul.bat", "w") as f:
        f.write(batch_content)
    
    print("Created launch script: run_deepsoul.bat")
    return True

def main():
    """Run the setup process"""
    print_header("DeepSoul Setup")
    
    if not check_python_version():
        sys.exit(1)
    
    check_gpu()
    
    if not install_dependencies():
        print("WARNING: Some dependencies failed to install.")
    
    create_directories()
    
    try:
        import torch
        create_config()
    except ImportError:
        print("WARNING: Could not create config file. PyTorch not installed.")
    
    create_batch_file()
    
    print_header("Setup Complete")
    print("""
DeepSoul has been set up successfully! You can now:

1. Run DeepSoul with:
   - Windows: Simply double-click run_deepsoul.bat
   - Command line: python deepsoul_launch.py

2. For help and available commands:
   Type 'help' at the DeepSoul prompt

3. If you encounter any issues:
   - Check that all dependencies are installed
   - Ensure you have enough disk space and RAM
   - For GPU usage, verify your CUDA installation

Enjoy using DeepSoul!
""")

if __name__ == "__main__":
    main()
