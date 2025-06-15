#!/usr/bin/env python3
"""
DeepSeek-Coder System Diagnostics Tool

This tool performs diagnostics on the system to help troubleshoot issues
with DeepSeek-Coder deployment and performance.
"""

import os
import sys
import json
import time
import platform
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import urllib.request
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DeepSoul-Diagnostics")

# Import optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from transformers import __version__ as transformers_version
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SystemDiagnostics:
    """System diagnostics for DeepSeek-Coder."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize diagnostics.
        
        Args:
            base_dir: Base directory for DeepSeek-Coder
        """
        self.base_dir = base_dir or os.getcwd()
        self.results: Dict[str, Any] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def run_all(self) -> Dict[str, Any]:
        """Run all diagnostic checks and return results."""
        logger.info("Starting system diagnostics")
        
        # Run all checks
        self.check_system_info()
        self.check_python_environment()
        self.check_pytorch()
        self.check_disk_space()
        self.check_memory()
        self.check_network()
        self.check_files()
        self.check_api_server()
        
        # Add summary
        self.results["summary"] = {
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
            "warnings": self.warnings,
            "errors": self.errors
        }
        
        logger.info(f"Diagnostics completed: {len(self.warnings)} warnings, {len(self.errors)} errors")
        return self.results
    
    def check_system_info(self):
        """Check system information."""
        logger.info("Checking system information")
        
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "processor": platform.processor(),
            "architecture": platform.machine()
        }
        
        # Check for container environment
        system_info["is_container"] = self._is_running_in_container()
        
        # Check for virtualization (Linux only)
        if platform.system() == "Linux" and PSUTIL_AVAILABLE:
            try:
                output = subprocess.check_output("systemd-detect-virt", shell=True, text=True).strip()
                system_info["virtualization"] = output
            except:
                system_info["virtualization"] = "unknown"
        
        # Check for WSL on Windows
        if platform.system() == "Windows":
            system_info["is_wsl"] = "Microsoft" in platform.release()
        
        # Check for MacOS hardware details
        if platform.system() == "Darwin":
            try:
                output = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True, text=True).strip()
                system_info["cpu_model"] = output
            except:
                pass
        
        self.results["system_info"] = system_info
    
    def _is_running_in_container(self) -> bool:
        """Check if running in a container."""
        # Check common container environments
        if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
            return True
        
        # Check cgroup (Linux-specific)
        try:
            with open("/proc/1/cgroup", "r") as f:
                content = f.read()
                if any(x in content for x in ["docker", "kubepods", "containerd"]):
                    return True
        except:
            pass
        
        return False
    
    def check_python_environment(self):
        """Check Python environment."""
        logger.info("Checking Python environment")
        
        env_info = {
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "python_path": sys.executable,
            "pip_packages": self._get_pip_packages()
        }
        
        # Check for virtual environment
        env_info["is_venv"] = sys.prefix != sys.base_prefix
        
        # Check critical packages for DeepSeek-Coder
        critical_packages = ["torch", "transformers", "accelerate", "fastapi", "uvicorn", "pydantic"]
        missing_packages = []
        
        for package in critical_packages:
            if package not in env_info["pip_packages"]:
                missing_packages.append(package)
        
        if missing_packages:
            warning = f"Missing critical packages: {', '.join(missing_packages)}"
            self.warnings.append(warning)
            env_info["missing_packages"] = missing_packages
        
        self.results["python_environment"] = env_info
    
    def _get_pip_packages(self) -> Dict[str, str]:
        """Get installed pip packages and versions."""
        packages = {}
        try:
            import pkg_resources
            for pkg in pkg_resources.working_set:
                packages[pkg.key] = pkg.version
        except:
            logger.warning("Could not get pip packages using pkg_resources")
            
            # Fallback to pip freeze
            try:
                output = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
                for line in output.splitlines():
                    if "==" in line:
                        name, version = line.split("==", 1)
                        packages[name.lower()] = version
            except:
                logger.warning("Could not get pip packages using pip freeze")
        
        return packages
    
    def check_pytorch(self):
        """Check PyTorch installation and GPU support."""
        logger.info("Checking PyTorch installation")
        
        torch_info = {
            "installed": TORCH_AVAILABLE
        }
        
        if not TORCH_AVAILABLE:
            self.warnings.append("PyTorch is not installed")
            self.results["pytorch"] = torch_info
            return
        
        # Get PyTorch version
        torch_info["version"] = torch.__version__
        
        # Check for CUDA support
        torch_info["cuda_available"] = torch.cuda.is_available()
        torch_info["cuda_version"] = torch.version.cuda if hasattr(torch.version, "cuda") else None
        
        if torch_info["cuda_available"]:
            torch_info["device_count"] = torch.cuda.device_count()
            torch_info["current_device"] = torch.cuda.current_device()
            torch_info["device_name"] = torch.cuda.get_device_name(torch_info["current_device"])
            
            # Check for NVIDIA drivers
            try:
                output = subprocess.check_output("nvidia-smi", shell=True, text=True)
                torch_info["nvidia_smi"] = True
            except:
                torch_info["nvidia_smi"] = False
                self.warnings.append("CUDA is available but nvidia-smi command failed")
            
            # Test a simple tensor operation
            try:
                start_time = time.time()
                a = torch.randn(1000, 1000, device="cuda")
                b = torch.randn(1000, 1000, device="cuda")
                c = torch.matmul(a, b)
                torch.cuda.synchronize()
                elapsed = time.time() - start_time
                torch_info["tensor_test_time"] = elapsed
            except Exception as e:
                torch_info["tensor_test_error"] = str(e)
                self.warnings.append(f"CUDA tensor operations failed: {str(e)}")
        else:
            self.warnings.append("CUDA is not available. GPU acceleration will not be used.")
        
        self.results["pytorch"] = torch_info
    
    def check_disk_space(self):
        """Check available disk space."""
        logger.info("Checking disk space")
        
        if not PSUTIL_AVAILABLE:
            self.results["disk_space"] = {"error": "psutil not installed"}
            return
        
        disk_info = {}
        
        # Check base directory
        try:
            usage = psutil.disk_usage(self.base_dir)
            disk_info["base_dir"] = {
                "path": self.base_dir,
                "total_gb": usage.total / (1024 ** 3),
                "free_gb": usage.free / (1024 ** 3),
                "used_gb": usage.used / (1024 ** 3),
                "percent_used": usage.percent
            }
            
            # Check if disk space is low
            if usage.free < 5 * (1024 ** 3):  # Less than 5GB free
                self.warnings.append(f"Low disk space on {self.base_dir}: {disk_info['base_dir']['free_gb']:.2f} GB free")
        except Exception as e:
            self.errors.append(f"Error checking disk space: {str(e)}")
        
        # Check model directory if it exists
        model_dir = os.path.join(self.base_dir, "models")
        if os.path.exists(model_dir):
            try:
                usage = psutil.disk_usage(model_dir)
                disk_info["model_dir"] = {
                    "path": model_dir,
                    "total_gb": usage.total / (1024 ** 3),
                    "free_gb": usage.free / (1024 ** 3),
                    "used_gb": usage.used / (1024 ** 3),
                    "percent_used": usage.percent
                }
                
                # Calculate model directory size
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(model_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                
                disk_info["model_dir"]["size_gb"] = total_size / (1024 ** 3)
            except Exception as e:
                self.warnings.append(f"Error analyzing model directory: {str(e)}")
        
        self.results["disk_space"] = disk_info
    
    def check_memory(self):
        """Check system memory."""
        logger.info("Checking memory")
        
        memory_info = {}
        
        # Check system memory
        if PSUTIL_AVAILABLE:
            try:
                vm = psutil.virtual_memory()
                memory_info["system"] = {
                    "total_gb": vm.total / (1024 ** 3),
                    "available_gb": vm.available / (1024 ** 3),
                    "used_gb": vm.used / (1024 ** 3),
                    "percent_used": vm.percent
                }
                
                # Check if memory is low
                if vm.available < 2 * (1024 ** 3):  # Less than 2GB free
                    self.warnings.append(f"Low system memory: {memory_info['system']['available_gb']:.2f} GB available")
            except Exception as e:
                self.warnings.append(f"Error checking system memory: {str(e)}")
        
        # Check GPU memory
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                gpu_info = []
                for i in range(torch.cuda.device_count()):
                    total_mem = torch.cuda.get_device_properties(i).total_memory
                    reserved_mem = torch.cuda.memory_reserved(i)
                    allocated_mem = torch.cuda.memory_allocated(i)
                    free_mem = total_mem - reserved_mem
                    
                    gpu_info.append({
                        "device": i,
                        "name": torch.cuda.get_device_name(i),
                        "total_gb": total_mem / (1024 ** 3),
                        "reserved_gb": reserved_mem / (1024 ** 3),
                        "allocated_gb": allocated_mem / (1024 ** 3),
                        "free_gb": free_mem / (1024 ** 3),
                        "utilization_percent": (allocated_mem / total_mem) * 100
                    })
                
                memory_info["gpu"] = gpu_info
            except Exception as e:
                self.warnings.append(f"Error checking GPU memory: {str(e)}")
        
        self.results["memory"] = memory_info
    
    def check_network(self):
        """Check network connectivity and configuration."""
        logger.info("Checking network")
        
        network_info = {}
        
        # Check internet connectivity
        try:
            # Try a simple connection to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            network_info["internet_connection"] = True
        except:
            network_info["internet_connection"] = False
            self.warnings.append("Internet connection not available")
        
        # Check HuggingFace connectivity
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get("https://huggingface.co", timeout=5)
                network_info["huggingface_connectivity"] = response.status_code == 200
                if not network_info["huggingface_connectivity"]:
                    self.warnings.append("Cannot connect to HuggingFace. Model downloads may fail.")
        except:
            network_info["huggingface_connectivity"] = False
            self.warnings.append("Cannot connect to HuggingFace. Model downloads may fail.")
        
        # Check API endpoint connectivity if running
        try:
            api_url = os.environ.get("DEEPSEEK_API_URL", "http://localhost:8000")
            if REQUESTS_AVAILABLE:
                response = requests.get(f"{api_url}/health", timeout=2)
                network_info["api_connectivity"] = response.status_code == 200
                if not network_info["api_connectivity"]:
                    self.warnings.append(f"Cannot connect to DeepSeek-Coder API at {api_url}")
        except:
            network_info["api_connectivity"] = False
        
        self.results["network"] = network_info
    
    def check_files(self):
        """Check for required files and directories."""
        logger.info("Checking files and directories")
        
        file_info = {"missing": [], "found": []}
        
        # Critical directories to check
        directories = {
            "models": os.path.join(self.base_dir, "models"),
            "logs": os.path.join(self.base_dir, "logs"),
            "data": os.path.join(self.base_dir, "data")
        }
        
        for name, path in directories.items():
            if os.path.exists(path):
                file_info["found"].append(path)
            else:
                file_info["missing"].append(path)
                self.warnings.append(f"Directory not found: {path}")
        
        # Critical files to check
        files = {
            "app.py": os.path.join(self.base_dir, "app.py"),
            "config": os.path.join(self.base_dir, ".env"),
            "requirements": os.path.join(self.base_dir, "requirements.txt"),
        }
        
        for name, path in files.items():
            if os.path.exists(path):
                file_info["found"].append(path)
            else:
                file_info["missing"].append(path)
                if name == "config":  # .env is not critical if environment variables are set directly
                    # Check if we have at least .env.example
                    if os.path.exists(os.path.join(self.base_dir, ".env.example")):
                        self.warnings.append(f"Config file not found: {path}. Using .env.example or environment variables.")
                    else:
                        self.warnings.append(f"Config file not found: {path}. Make sure environment variables are set.")
                else:
                    self.errors.append(f"Critical file not found: {path}")
        
        # Check model files if directory exists
        model_dir = directories["models"]
        if os.path.exists(model_dir):
            # Check for model files with common extensions
            model_files = []
            for ext in [".bin", ".pt", ".pth", ".safetensors", ".gguf"]:
                model_files.extend(list(Path(model_dir).glob(f"**/*{ext}")))
            
            file_info["model_files"] = [str(f) for f in model_files]
            
            if not model_files:
                self.warnings.append(f"No model files found in {model_dir}")
            else:
                logger.info(f"Found {len(model_files)} model files")
        
        self.results["files"] = file_info
    
    def check_api_server(self):
        """Check API server status and configuration."""
        logger.info("Checking API server")
        
        api_info = {}
        
        # Get API URL from environment or use default
        api_url = os.environ.get("DEEPSEEK_API_URL", "http://localhost:8000")
        api_info["url"] = api_url
        
        # Check if the API is running
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(f"{api_url}/health", timeout=5)
                api_info["status"] = response.status_code
                api_info["running"] = response.status_code == 200
                
                if response.status_code == 200:
                    # Parse response and extract info
                    try:
                        data = response.json()
                        api_info["health_data"] = data
                        api_info["model"] = data.get("model", "unknown")
                        logger.info(f"API running with model: {api_info['model']}")
                    except:
                        self.warnings.append("API is running but returned invalid health check data")
                else:
                    self.warnings.append(f"API health check failed with status {response.status_code}")
            else:
                api_info["running"] = False
                self.warnings.append("Cannot check API: requests package not installed")
        except Exception as e:
            api_info["running"] = False
            api_info["error"] = str(e)
            self.warnings.append(f"API connection error: {str(e)}")
        
        # Check API key if provided
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if api_key:
            api_info["api_key_provided"] = True
            
            # Test API key if server is running
            if api_info.get("running") and REQUESTS_AVAILABLE:
                try:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    # Make a simple request to test authentication
                    response = requests.post(
                        f"{api_url}/api/v1/completion",
                        headers=headers,
                        json={"prompt": "test", "max_tokens": 1},
                        timeout=5
                    )
                    api_info["auth_status"] = response.status_code
                    if response.status_code == 401:
                        self.warnings.append("API key authentication failed. Check your API key.")
                except Exception as e:
                    api_info["auth_error"] = str(e)
        else:
            api_info["api_key_provided"] = False
            self.warnings.append("No API key provided in environment. Authentication may fail.")
        
        # Check environment configuration
        env_vars = [
            "MODEL_SIZE", "LOG_LEVEL", "PORT", "HOST", "ENABLE_AUTH", 
            "DATA_DIR", "LOG_DIR", "CACHE_DIR", "CUDA_VISIBLE_DEVICES"
        ]
        
        config = {var: os.environ.get(var) for var in env_vars if os.environ.get(var) is not None}
        api_info["env_config"] = config
        
        self.results["api_server"] = api_info
    
    def run_benchmarks(self):
        """Run basic performance benchmarks."""
        logger.info("Running benchmarks")
        
        if not TORCH_AVAILABLE:
            self.results["benchmarks"] = {"error": "PyTorch not installed"}
            return
        
        benchmark_results = {}
        
        # CPU benchmark - matrix multiplication
        try:
            sizes = [1000, 2000]
            cpu_times = []
            
            for size in sizes:
                start_time = time.time()
                a = torch.randn(size, size)
                b = torch.randn(size, size)
                c = torch.matmul(a, b)
                elapsed = time.time() - start_time
                cpu_times.append((size, elapsed))
            
            benchmark_results["cpu"] = {
                "matrix_mul": {f"{size}x{size}": elapsed for size, elapsed in cpu_times}
            }
        except Exception as e:
            benchmark_results["cpu"] = {"error": str(e)}
        
        # GPU benchmark if available
        if torch.cuda.is_available():
            try:
                sizes = [1000, 2000, 4000, 8000]
                gpu_times = []
                
                for size in sizes:
                    try:
                        # Skip larger sizes if we're running out of memory
                        a = torch.randn(size, size, device="cuda")
                        b = torch.randn(size, size, device="cuda")
                        
                        # Warmup
                        _ = torch.matmul(a, b)
                        torch.cuda.synchronize()
                        
                        # Timed run
                        start_time = time.time()
                        c = torch.matmul(a, b)
                        torch.cuda.synchronize()
                        elapsed = time.time() - start_time
                        
                        gpu_times.append((size, elapsed))
                    except RuntimeError:
                        # Out of memory, stop testing larger sizes
                        self.warnings.append(f"GPU out of memory on {size}x{size} matrix")
                        break
                
                benchmark_results["gpu"] = {
                    "matrix_mul": {f"{size}x{size}": elapsed for size, elapsed in gpu_times}
                }
            except Exception as e:
                benchmark_results["gpu"] = {"error": str(e)}
        
        self.results["benchmarks"] = benchmark_results
        
    def export_results(self, output_path: Optional[str] = None):
        """Export results to a JSON file."""
        if not output_path:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            output_path = os.path.join(self.base_dir, f"diagnostics_{timestamp}.json")
        
        try:
            with open(output_path, "w") as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Diagnostic results saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            return None


def main():
    parser = argparse.ArgumentParser(description="DeepSeek-Coder System Diagnostics")
    parser.add_argument("--dir", help="DeepSeek-Coder base directory (default: current directory)")
    parser.add_argument("--output", help="Output file path for results (default: diagnostics_TIMESTAMP.json)")
    parser.add_argument("--benchmarks", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create diagnostics object
    diagnostics = SystemDiagnostics(args.dir)
    
    # Run diagnostics
    results = diagnostics.run_all()
    
    # Run benchmarks if requested
    if args.benchmarks:
        diagnostics.run_benchmarks()
    
    # Export results
    output_path = diagnostics.export_results(args.output)
    
    # Print summary
    print("\nDiagnostic Results Summary:")
    print("=" * 80)
    print(f"Warnings: {len(diagnostics.warnings)}")
    print(f"Errors: {len(diagnostics.errors)}")
    
    # Print warnings and errors
    if diagnostics.warnings:
        print("\nWarnings:")
        for i, warning in enumerate(diagnostics.warnings, 1):
            print(f"{i}. {warning}")
    
    if diagnostics.errors:
        print("\nErrors:")
        for i, error in enumerate(diagnostics.errors, 1):
            print(f"{i}. {error}")
    
    # Print path to results file
    if output_path:
        print(f"\nFull diagnostic results saved to: {output_path}")
    
    # Exit with error code if there were errors
    return 1 if diagnostics.errors else 0


if __name__ == "__main__":
    sys.exit(main())
