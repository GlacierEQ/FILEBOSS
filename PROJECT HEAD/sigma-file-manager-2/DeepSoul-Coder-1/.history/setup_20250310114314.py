#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from pathlib import Path
import shutil
import platform
import time
import json
from typing import Dict, List, Optional, Tuple, Union


def print_section(title):
    """Print a section title with formatting."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_command(command, description=None, check=True):
    """Run a shell command and print its output."""
    if description:
        print(f"\n>> {description}")
    print(f"$ {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if result.stdout and result.stdout.strip():
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        if e.stdout:
            print(e.stdout)
        return False, e.stdout


def check_environment():
    """Check and print system environment details."""
    print_section("Checking System Environment")
    
    # Check Python version
    python_version = platform.python_version()
    print(f"Python version: {python_version}")
    if not (3, 8) <= tuple(map(int, python_version.split('.')[:2])) <= (3, 11):
        print("WARNING: Recommended Python version is 3.8-3.11")
    
    # Check if CUDA is available
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"CUDA available: {cuda_available}")
        if cuda_available:
            cuda_version = torch.version.cuda
            print(f"CUDA version: {cuda_version}")
            device_count = torch.cuda.device_count()
            print(f"GPU count: {device_count}")
            for i in range(device_count):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"    Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
    except ImportError:
        print("PyTorch not installed yet. CUDA availability will be checked after installation.")
    
    # Check for NPU support (Intel/AMD/Apple)
    try:
        print("\nChecking for NPU support:")
        
        # Check for Intel Neural Compute Stick / OpenVINO
        has_openvino = False
        try:
            import openvino
            has_openvino = True
            print("  OpenVINO detected:", openvino.__version__)
        except ImportError:
            print("  OpenVINO not found")
        
        # Check for Apple Neural Engine (MPS)
        has_mps = False
        if platform.system() == "Darwin":  # macOS
            try:
                if torch.backends.mps.is_available():
                    has_mps = True
                    print("  Apple Neural Engine (MPS) detected")
                else:
                    print("  Apple Neural Engine (MPS) not available")
            except:
                print("  Could not detect Apple Neural Engine")
        
        # Check for AMD ROCm
        has_rocm = False
        try:
            if torch.__version__ and hasattr(torch, 'version') and hasattr(torch.version, 'hip'):
                has_rocm = True
                print("  AMD ROCm detected:", torch.version.hip)
            else:
                print("  AMD ROCm not detected")
        except:
            print("  Could not check for AMD ROCm")
            
        # Check for DirectML
        has_directml = False
        if platform.system() == "Windows":
            try:
                import torch_directml
                has_directml = True
                print("  DirectML detected:", torch_directml.__version__)
            except ImportError:
                print("  DirectML not found")
        
        # Store in environment info for later use
        npu_info = {
            "openvino": has_openvino,
            "mps": has_mps,
            "rocm": has_rocm,
            "directml": has_directml
        }
        print("  NPU support summary:", ", ".join([k for k, v in npu_info.items() if v]))
        
    except Exception as e:
        print(f"  Error checking NPU support: {e}")
    
    # Check disk space
    if platform.system() == "Windows":
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(os.getcwd()),
                                                 None, None, ctypes.pointer(free_bytes))
        free_gb = free_bytes.value / (1024**3)
    else:
        stat = os.statvfs(os.getcwd())
        free_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
    
    print(f"Free disk space: {free_gb:.2f} GB")
    if free_gb < 20:
        print("WARNING: Less than 20GB of free space available. Models and datasets may require more.")
    
    # Check for git
    git_available, git_version = run_command("git --version", check=False)
    if git_available:
        print("Git is available:", git_version.strip() if git_version else "Version unknown")
    else:
        print("WARNING: Git is not available. Some dataset downloads may not work properly.")
    
    # Check for CPU info
    if platform.system() == "Linux":
        run_command("lscpu | grep 'Model name\\|CPU(s)\\|Thread'", "CPU Information", check=False)
    elif platform.system() == "Darwin":  # macOS
        run_command("sysctl -n machdep.cpu.brand_string", "CPU Model", check=False)
        run_command("sysctl -n hw.ncpu", "CPU Count", check=False)
    elif platform.system() == "Windows":
        run_command("wmic cpu get name, numberofcores, numberoflogicalprocessors", "CPU Information", check=False)
    
    # Check RAM
    if platform.system() == "Linux":
        run_command("free -h", "Memory Information", check=False)
    elif platform.system() == "Darwin":  # macOS
        run_command("sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 \" GB\"}'", "Total Memory", check=False)
    elif platform.system() == "Windows":
        run_command("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value", "Memory Information", check=False)
    
    # Check for pip and pip version
    run_command("pip --version", "Pip version", check=False)
    
    # Save environment info to a file
    env_info = {
        "python_version": python_version,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "free_disk_space_gb": round(free_gb, 2),
        "cuda_available": cuda_available if 'cuda_available' in locals() else False,
        "npu_support": npu_info if 'npu_info' in locals() else {},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        with open("environment_info.json", "w") as f:
            json.dump(env_info, f, indent=2)
        print("\nEnvironment information saved to environment_info.json")
    except Exception as e:
        print(f"Could not save environment information: {e}")


def install_base_dependencies():
    """Install base dependencies required for all components."""
    print_section("Installing Base Dependencies")
    
    # Install PyTorch first according to hardware availability
    try:
        import torch
        print("PyTorch already installed.")
    except ImportError:
        print("\nInstalling PyTorch...")
        
        # Check for available hardware
        nvidia_smi = shutil.which("nvidia-smi")
        
        # Check for Apple Silicon
        is_apple_silicon = False
        if platform.system() == "Darwin" and platform.machine() == "arm64":
            is_apple_silicon = True
            print("Apple Silicon (M1/M2/M3) detected, installing PyTorch with MPS support")
            run_command("pip install torch torchvision torchaudio")
        # Check for NVIDIA GPU
        elif nvidia_smi:
            print("NVIDIA GPU detected, installing PyTorch with CUDA support")
            run_command("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        else:
            # Check for AMD GPU on Windows
            if platform.system() == "Windows":
                print("Installing PyTorch CPU version with DirectML support for Windows")
                run_command("pip install torch torchvision torchaudio")
                run_command("pip install torch-directml")
            # Check for AMD GPU on Linux with ROCm
            elif platform.system() == "Linux" and os.path.exists("/opt/rocm"):
                print("AMD GPU with ROCm detected, installing PyTorch with ROCm support")
                run_command("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.2")
            else:
                print("No specialized AI hardware detected, installing PyTorch CPU version")
                run_command("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    
    # Check if requirements.txt exists
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print(f"WARNING: {req_file} not found. Creating a basic requirements file.")
        with open(req_file, "w") as f:
            f.write("# Basic requirements for DeepSeek-Coder\n")
            f.write("transformers>=4.30.0\n")
            f.write("accelerate>=0.20.0\n")
            f.write("datasets>=2.10.0\n")
            f.write("huggingface-hub>=0.16.0\n")
    
    # Install base requirements
    run_command("pip install -r requirements.txt")
    
    # Check and install git LFS if needed
    try:
        success, output = run_command("git lfs install", check=False)
        if not success or "not a git command" in (output or "").lower():
            print("\nGit LFS not found. It's recommended for downloading large model files.")
            print("Please install Git LFS: https://git-lfs.github.com/")
    except Exception as e:
        print(f"Could not check Git LFS: {e}")


def install_evaluation_dependencies():
    """Install dependencies for the evaluation modules."""
    print_section("Installing Evaluation Dependencies")
    
    # HumanEval dependencies
    print("\n>> Installing HumanEval dependencies")
    run_command("pip install accelerate attrdict transformers")
    
    # MBPP dependencies
    print("\n>> Installing MBPP dependencies")
    run_command("pip install tqdm")
    
    # PAL-Math dependencies
    print("\n>> Installing PAL-Math dependencies")
    run_command("pip install sympy==1.12 pebble timeout-decorator regex multiprocess")
    
    # DS-1000 dependencies
    print("\n>> Installing DS-1000 dependencies")
    run_command("pip install pandas matplotlib seaborn scikit-learn numpy")
    
    # LeetCode dependencies - check if specific ones are needed
    print("\n>> Installing LeetCode dependencies")
    run_command("pip install vllm")
    
    # Check if all evaluation directories exist, create if not
    eval_dirs = ["Evaluation/HumanEval", "Evaluation/MBPP", "Evaluation/PAL-Math", 
                 "Evaluation/LeetCode", "Evaluation/DS-1000"]
    
    for dir_path in eval_dirs:
        if not os.path.exists(dir_path):
            print(f"Creating directory {dir_path}")
            os.makedirs(dir_path, exist_ok=True)


def install_finetune_dependencies():
    """Install dependencies for the fine-tuning module."""
    print_section("Installing Fine-tuning Dependencies")
    
    finetune_req = Path("finetune/requirements.txt")
    if not finetune_req.exists():
        print(f"WARNING: {finetune_req} not found. Creating a basic finetune requirements file.")
        os.makedirs("finetune", exist_ok=True)
        with open(finetune_req, "w") as f:
            f.write("# Requirements for DeepSeek-Coder fine-tuning\n")
            f.write("transformers>=4.30.0\n")
            f.write("deepspeed>=0.9.0\n")
            f.write("accelerate>=0.20.0\n")
            f.write("datasets>=2.10.0\n")
            f.write("torch>=2.0.0\n")
            f.write("tensorboard>=2.12.0\n")
    
    run_command("pip install -r finetune/requirements.txt")
    
    # Check if DeepSpeed is properly installed
    if not run_command("python -c \"import deepspeed; print('DeepSpeed version:', deepspeed.__version__)\"", 
                     "Checking DeepSpeed installation")[0]:
        print("\nInstalling DeepSpeed with CUDA extensions...")
        run_command("pip install deepspeed")
        
    # Check if the DeepSpeed configuration file exists
    ds_config = Path("finetune/configs/ds_config_zero3.json")
    if not ds_config.exists():
        print(f"Creating DeepSpeed configuration directory and file {ds_config}")
        os.makedirs("finetune/configs", exist_ok=True)
        with open(ds_config, "w") as f:
            f.write('''{
    "bf16": {
        "enabled": "auto"
    },
    "zero_optimization": {
        "stage": 3,
        "offload_optimizer": {
            "device": "cpu",
            "pin_memory": true
        },
        "offload_param": {
            "device": "cpu",
            "pin_memory": true
        },
        "overlap_comm": true,
        "contiguous_gradients": true,
        "sub_group_size": 1e9,
        "reduce_bucket_size": "auto",
        "stage3_prefetch_bucket_size": "auto",
        "stage3_param_persistence_threshold": "auto",
        "stage3_max_live_parameters": 1e9,
        "stage3_max_reuse_distance": 1e9,
        "gather_16bit_weights_on_model_save": true
    },
    "gradient_accumulation_steps": "auto",
    "gradient_clipping": "auto",
    "steps_per_print": 10,
    "train_batch_size": "auto",
    "train_micro_batch_size_per_gpu": "auto",
    "wall_clock_breakdown": false
}''')


def install_demo_dependencies():
    """Install dependencies for the demo."""
    print_section("Installing Demo Dependencies")
    
    demo_req = Path("demo/requirements.txt")
    if not demo_req.exists():
        print(f"WARNING: {demo_req} not found. Creating basic demo requirements file.")
        os.makedirs("demo", exist_ok=True)
        with open(demo_req, "w") as f:
            f.write("# Requirements for DeepSeek-Coder demo\n")
            f.write("gradio>=3.50.0\n")
            f.write("transformers>=4.30.0\n")
            f.write("torch>=2.0.0\n")
            f.write("accelerate>=0.20.0\n")
    
    run_command("pip install -r demo/requirements.txt")


def check_datasets():
    """Check if evaluation datasets are available and provide download info."""
    print_section("Checking Datasets")
    
    datasets = {
        "HumanEval": {
            "path": "Evaluation/HumanEval/data",
            "download_url": "https://github.com/openai/human-eval"
        },
        "MBPP": {
            "path": "Evaluation/MBPP/data",
            "download_url": "https://github.com/google-research/google-research/tree/master/mbpp"
        },
        "PAL-Math": {
            "path": "Evaluation/PAL-Math/datasets",
            "download_url": "https://github.com/reasoning-machines/pal"
        },
        "LeetCode": {
            "path": "Evaluation/LeetCode/data",
            "download_url": "https://github.com/facebookresearch/CodeGen/tree/main/evaluation"
        },
        "DS-1000": {
            "path": "Evaluation/DS-1000",
            "download_url": "https://github.com/xlang-ai/DS-1000"
        }
    }
    
    for name, info in datasets.items():
        path = info["path"]
        full_path = Path(path)
        if full_path.exists():
            print(f"{name} dataset: Found at {full_path.absolute()}")
            # Count files to give a basic idea
            files = list(full_path.glob("**/*"))
            print(f"  Contains {len(files)} files/directories")
        else:
            print(f"{name} dataset: Not found at {full_path.absolute()}")
            print(f"  Please download the dataset from: {info['download_url']}")
            print(f"  And place it in the {path} directory.")
            
            # Create the directory if it doesn't exist
            os.makedirs(full_path, exist_ok=True)
            print(f"  Directory {path} created.")


def setup_model_cache():
    """Set up the model cache directory and environment variable."""
    print_section("Setting Up Model Cache")
    
    # Determine the best location for the cache
    if platform.system() == "Windows":
        default_cache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    else:
        default_cache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    
    cache_dir = os.environ.get("TRANSFORMERS_CACHE", default_cache)
    print(f"Current HuggingFace cache directory: {cache_dir}")
    
    # Check if the cache directory exists and has enough space
    try:
        os.makedirs(cache_dir, exist_ok=True)
        print(f"Cache directory exists or was created: {cache_dir}")
        
        # Check space in cache directory
        if platform.system() == "Windows":
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(cache_dir),
                                                      None, None, ctypes.pointer(free_bytes))
            free_gb = free_bytes.value / (1024**3)
        else:
            stat = os.statvfs(cache_dir)
            free_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
        
        print(f"Free space in cache directory: {free_gb:.2f} GB")
        if free_gb < 50:
            print("WARNING: The cache directory has less than 50GB of free space.")
            print("Large models like DeepSeek-Coder-33B may require more space.")
    except Exception as e:
        print(f"Warning: Could not check or create cache directory: {e}")


def print_usage_instructions():
    """Print instructions on how to use the codebase."""
    print_section("Usage Instructions")
    
    print("""
DeepSeek-Coder environment is now set up. Here's how to use the different components:

1. Evaluate on HumanEval:
   cd Evaluation/HumanEval
   python -m accelerate.commands.launch --config_file test_config.yaml eval_pal.py --logdir MODEL_PATH --language LANGUAGE --dataroot data/

2. Evaluate on MBPP:
   cd Evaluation/MBPP
   python -m accelerate.commands.launch --config_file test_config.yaml eval_pal.py --logdir MODEL_PATH --language python --dataroot data/

3. Evaluate on PAL-Math:
   cd Evaluation/PAL-Math
   python run.py --data_name gsm8k --model_name_or_path MODEL_PATH --batch_size 16 --do_inference

4. Run demo:
   cd demo
   python app.py

5. Fine-tune model:
   cd finetune
   deepspeed finetune_deepseekcoder.py --model_name_or_path MODEL_PATH --data_path DATA_PATH --output_dir OUTPUT_PATH [additional arguments]

Refer to README.md files in each directory for more detailed instructions and options.
""")


def setup_virtual_env(venv_name="deepseek_env"):
    """Set up a virtual environment for DeepSeek-Coder."""
    print_section(f"Setting Up Virtual Environment: {venv_name}")
    
    venv_dir = Path(venv_name)
    if venv_dir.exists():
        print(f"Virtual environment {venv_name} already exists.")
        return True
    
    # Check if venv module is available
    success, _ = run_command("python -m venv --help", "Checking venv module", check=False)
    if not success:
        print("Python venv module not available. Please install it or create a virtual environment manually.")
        return False
    
    # Create virtual environment
    success, _ = run_command(f"python -m venv {venv_name}", f"Creating virtual environment {venv_name}")
    if not success:
        print(f"Failed to create virtual environment {venv_name}.")
        return False
    
    # Activate and install pip in the virtual environment
    activate_script = "activate" if platform.system() != "Windows" else "Scripts\\activate"
    if platform.system() == "Windows":
        print(f"Virtual environment created. To activate it, run:\n{venv_name}\\Scripts\\activate.bat")
    else:
        print(f"Virtual environment created. To activate it, run:\nsource {venv_name}/{activate_script}")
    
    return True


def download_test_model():
    """Download a small test model to verify setup."""
    print_section("Downloading Test Model")
    
    print("This will download a small model to test your setup.")
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("Downloading test tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-coder-1.3b-base", trust_remote_code=True)
        
        print("Downloading test model (this might take a few minutes)...")
        model = AutoModelForCausalLM.from_pretrained("deepseek-ai/deepseek-coder-1.3b-base", 
                                                   torch_dtype=torch.float16, 
                                                   trust_remote_code=True)
        
        print("Test model downloaded successfully.")
        return True
    except Exception as e:
        print(f"Failed to download test model: {e}")
        return False


def generate_test_completion():
    """Generate a simple code completion to test the model."""
    print_section("Testing Model with Simple Completion")
    
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        print("Loading model and tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/deepseek-coder-1.3b-base", trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained("deepseek-ai/deepseek-coder-1.3b-base", 
                                                   torch_dtype=torch.float16, 
                                                   trust_remote_code=True)
        
        if torch.cuda.is_available():
            model = model.cuda()
        
        input_text = "def fibonacci(n):"
        print(f"Generating completion for: {input_text}")
        
        inputs = tokenizer(input_text, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        
        outputs = model.generate(**inputs, max_length=100)
        completion = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print("\nGenerated completion:")
        print("-" * 40)
        print(completion)
        print("-" * 40)
        
        return True
    except Exception as e:
        print(f"Failed to test model: {e}")
        return False


def main():
    """Main function to handle command-line arguments and run the setup."""
    parser = argparse.ArgumentParser(description="Set up DeepSeek-Coder environment")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--eval-only", action="store_true", help="Only install evaluation dependencies")
    parser.add_argument("--finetune-only", action="store_true", help="Only install fine-tuning dependencies")
    parser.add_argument("--demo-only", action="store_true", help="Only install demo dependencies")
    parser.add_argument("--create-venv", action="store_true", help="Create a virtual environment")
    parser.add_argument("--venv-name", type=str, default="deepseek_env", help="Virtual environment name")
    parser.add_argument("--test-model", action="store_true", help="Download and test a small model")
    parser.add_argument("--setup-model-cache", action="store_true", help="Set up the model cache directory")
    parser.add_argument("--npu-support", action="store_true", help="Install NPU support packages")
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    # Welcome message
    print_section("DeepSeek-Coder Setup")
    print("This script will set up the environment for DeepSeek-Coder.")
    
    # Create virtual environment if requested
    if args.create_venv:
        if not setup_virtual_env(args.venv_name):
            print("Failed to create virtual environment. Continuing with system Python.")
    
    # Check environment regardless of other options
    check_environment()
    
    if not args.skip_deps:
        # If no specific flag is set, install everything
        install_everything = not (args.eval_only or args.finetune_only or args.demo_only)
        
        # Install base dependencies if installing everything or any component
        install_base_dependencies()
        
        if install_everything or args.eval_only:
            install_evaluation_dependencies()
        
        if install_everything or args.finetune_only:
            install_finetune_dependencies()
        
        if install_everything or args.demo_only:
            install_demo_dependencies()
    
    # Set up model cache if requested
    if args.setup_model_cache:
        setup_model_cache()
    
    # Install NPU support if requested
    if args.npu_support:
        print_section("Installing NPU Support Packages")
        system = platform.system()
        
        if system == "Darwin" and platform.machine() == "arm64":
            print("Apple Neural Engine (MPS) is already supported by your PyTorch installation")
        elif system == "Windows":
            print("Installing DirectML support for Windows...")
            run_command("pip install torch-directml")
        elif system == "Linux":
            print("Installing OpenVINO support...")
            run_command("pip install openvino openvino-dev")
            
            if os.path.exists("/opt/rocm"):
                print("ROCm detected, PyTorch ROCm support should be already installed")
            else:
                print("No specific NPU hardware detected on Linux")
    
    # Check datasets regardless of dependency installation
    check_datasets()
    
    # Download and test a model if requested
    if args.test_model:
        download_test_model()
        generate_test_completion()
    
    # Print usage instructions
    print_usage_instructions()
    
    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    
    print_section("Setup Complete")
    print(f"DeepSeek-Coder environment is now ready to use!")
    print(f"Setup completed in {int(minutes)} minutes and {int(seconds)} seconds.")


if __name__ == "__main__":
    main()
