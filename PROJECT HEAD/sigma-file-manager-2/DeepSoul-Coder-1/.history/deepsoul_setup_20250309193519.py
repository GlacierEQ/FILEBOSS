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

def detect_nodejs():
    """Detect Node.js installation and return the executable path"""
    print_header("Detecting Node.js")
    
    nodejs_path = None
    
    # Check if node is in PATH
    try:
        if os.name == 'nt':  # Windows
            # Use where command on Windows
            result = subprocess.run(['where', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                nodejs_path = result.stdout.strip().split('\n')[0]
        else:  # macOS/Linux
            # Try which command first
            result = subprocess.run(['which', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                nodejs_path = result.stdout.strip()
            else:
                # Check common NVM locations
                home = os.path.expanduser("~")
                nvm_paths = [
                    os.path.join(home, ".nvm/versions/node"),
                    os.path.join(home, ".nodenv/versions")
                ]
                
                for nvm_path in nvm_paths:
                    if os.path.exists(nvm_path):
                        # Find the highest version
                        versions = sorted([d for d in os.listdir(nvm_path) if d.startswith('v')], 
                                        key=lambda x: [int(n) for n in x[1:].split('.')])
                        if versions:
                            latest = os.path.join(nvm_path, versions[-1], 'bin', 'node')
                            if os.path.exists(latest):
                                nodejs_path = latest
                                break
        
        # Test if node works
        if nodejs_path:
            version_cmd = [nodejs_path, '--version']
            result = subprocess.run(version_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"Node.js detected: {node_version}")
                print(f"Node.js path: {nodejs_path}")
            else:
                print("Node.js executable found but failed to run version check")
                nodejs_path = None
        
    except Exception as e:
        print(f"Error detecting Node.js: {str(e)}")
    
    if not nodejs_path:
        print("Node.js not found. Some JavaScript-related features may not be available.")
    
    return nodejs_path

def save_environment_info(info_dict):
    """Save environment information to a file"""
    env_file = "deepsoul_config/environment_info.json"
    os.makedirs(os.path.dirname(env_file), exist_ok=True)
    
    import json
    with open(env_file, "w") as f:
        json.dump(info_dict, f, indent=2)
    
    print(f"Environment info saved to: {env_file}")

def main():
    """Run the setup process"""
    print_header("DeepSoul Setup")
    
    if not check_python_version():
        sys.exit(1)
    
    check_gpu()
    
    # Detect Node.js
    nodejs_path = detect_nodejs()
    
    if not install_dependencies():
        print("WARNING: Some dependencies failed to install.")
    
    create_directories()
    
    try:
        import torch
        create_config()
        
        # Save environment information
        env_info = {
            "python_version": platform.python_version(),
            "os_platform": platform.platform(),
            "cuda_available": torch.cuda.is_available(),
            "nodejs_path": nodejs_path,
            "setup_time": import_datetime_and_get_now()
        }
        save_environment_info(env_info)
        
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

def import_datetime_and_get_now():
    """Import datetime and return current time as string"""
    from datetime import datetime
    return datetime.now().isoformat()

if __name__ == "__main__":
    main()
