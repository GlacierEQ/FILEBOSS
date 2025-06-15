#!/usr/bin/env python3
"""
Memory Protection Setup - Configure memory protection for DeepSeek-Coder
"""
import os
import sys
import json
import torch
import psutil
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import memory manager
from utils.memory_manager import get_memory_manager, setup_memory_protection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("memory_protection_setup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MemoryProtectionSetup")

def detect_system_specs():
    """Detect system specifications for memory configuration"""
    specs = {
        "total_ram": psutil.virtual_memory().total,
        "available_ram": psutil.virtual_memory().available,
        "cpu_cores": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True)
    }
    
    # Detect GPU information
    specs["cuda_available"] = torch.cuda.is_available()
    specs["gpu_count"] = torch.cuda.device_count() if specs["cuda_available"] else 0
    
    if specs["cuda_available"]:
        specs["gpus"] = []
        for i in range(specs["gpu_count"]):
            gpu_info = {
                "name": torch.cuda.get_device_name(i),
                "total_memory": torch.cuda.get_device_properties(i).total_memory
            }
            specs["gpus"].append(gpu_info)
    
    return specs

def create_memory_config(specs):
    """Create memory configuration based on system specifications"""
    # Convert bytes to GB for human-readable values
    total_ram_gb = specs["total_ram"] / (1024**3)
    available_ram_gb = specs["available_ram"] / (1024**3)
    
    # Calculate optimal thresholds based on available memory
    if total_ram_gb < 8:
        # Low memory system
        ram_warning = 0.75  # 75%
        ram_critical = 0.85  # 85%
    elif total_ram_gb < 16:
        # Medium memory system
        ram_warning = 0.80  # 80%
        ram_critical = 0.90  # 90%
    else:
        # High memory system
        ram_warning = 0.85  # 85%
        ram_critical = 0.95  # 95%
    
    # Calculate GPU thresholds
    if specs["cuda_available"] and specs["gpu_count"] > 0:
        gpu_warning = 0.80  # 80%
        gpu_critical = 0.90  # 90%
        
        # Check for specific known GPUs with memory issues
        for gpu in specs["gpus"]:
            if "1650" in gpu["name"] or "1050" in gpu["name"]:
                # Lower thresholds for GPUs known to have memory issues
                gpu_warning = 0.75
                gpu_critical = 0.85
    else:
        gpu_warning = 0.80
        gpu_critical = 0.90
    
    # Create configuration
    config = {
        "memory_protection": {
            "enabled": True,
            "ram_warning_threshold": ram_warning,
            "ram_critical_threshold": ram_critical,
            "gpu_warning_threshold": gpu_warning,
            "gpu_critical_threshold": gpu_critical,
            "check_interval": 3.0,  # seconds
            "memory_dump_enabled": True,
            "auto_offload_to_cpu": True,
            "aggressive_gc": True
        },
        "system_specs": {
            "total_ram_gb": total_ram_gb,
            "available_ram_gb": available_ram_gb,
            "cuda_available": specs["cuda_available"],
            "gpu_count": specs["gpu_count"]
        }
    }
    
    # Add GPU-specific configurations
    if specs["cuda_available"] and specs["gpu_count"] > 0:
        config["gpus"] = []
        
        for i, gpu in enumerate(specs["gpus"]):
            gpu_config = {
                "id": i,
                "name": gpu["name"],
                "total_memory_gb": gpu["total_memory"] / (1024**3),
                "warning_threshold": gpu_warning,
                "critical_threshold": gpu_critical,
                "monitoring_enabled": True
            }
            config["gpus"].append(gpu_config)
    
    return config

def save_config(config):
    """Save memory configuration to file"""
    config_path = Path("deepsoul_config/memory_config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Memory configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving memory configuration: {str(e)}")
        return False

def custom_warning_hook(data):
    """Custom warning hook for memory protection"""
    if "gpu_usage" in data:
        gpu_id = data.get("gpu_id", 0)
        usage = data["gpu_usage"]
        logger.warning(f"High GPU {gpu_id} memory usage detected: {usage:.1%}")
        logger.warning("Consider using smaller batch sizes or reducing model precision")
    elif "ram_usage" in data:
        usage = data["ram_usage"]
        logger.warning(f"High RAM usage detected: {usage:.1%}")
        logger.warning("Cleaning caches and temporary data")

def custom_critical_hook(data):
    """Custom critical hook for memory protection"""
    if "gpu_usage" in data:
        gpu_id = data.get("gpu_id", 0)
        usage = data["gpu_usage"]
        logger.critical(f"Critical GPU {gpu_id} memory usage: {usage:.1%}")
        logger.critical("Emergency measures: Offloading to CPU, clearing cache")
        
        # Get memory manager and create dump
        memory_manager = get_memory_manager()
        memory_manager.memory_dump(f"critical_gpu{gpu_id}")
        
        # Emergency cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
    elif "ram_usage" in data:
        usage = data["ram_usage"]
        logger.critical(f"Critical RAM usage: {usage:.1%}")
        logger.critical("Emergency measures: Aggressive memory cleanup")
        
        # Get memory manager and create dump
        memory_manager = get_memory_manager()
        memory_manager.memory_dump("critical_ram")

def setup():
    """Main setup function"""
    logger.info("Starting memory protection setup")
    
    # Detect system specifications
    logger.info("Detecting system specifications...")
    specs = detect_system_specs()
    
    # Log system specifications
    logger.info(f"Total RAM: {specs['total_ram'] / (1024**3):.2f} GB")
    logger.info(f"Available RAM: {specs['available_ram'] / (1024**3):.2f} GB")
    logger.info(f"CPU: {specs['cpu_cores']} cores, {specs['cpu_threads']} threads")
    
    if specs["cuda_available"]:
        logger.info(f"CUDA available with {specs['gpu_count']} GPU(s)")
        for i, gpu in enumerate(specs["gpus"]):
            logger.info(f"  GPU {i}: {gpu['name']} ({gpu['total_memory'] / (1024**3):.2f} GB)")
    else:
        logger.info("CUDA not available, using CPU only")
    
    # Create memory configuration
    logger.info("Creating memory configuration...")
    config = create_memory_config(specs)
    
    # Save configuration
    save_config(config)
    
    # Set up memory protection with custom hooks
    logger.info("Setting up memory protection with custom hooks...")
    setup_memory_protection(
        warning_hook=custom_warning_hook,
        critical_hook=custom_critical_hook
    )
    
    # Create memory dumps directory if it doesn't exist
    Path("memory_dumps").mkdir(exist_ok=True)
    
    logger.info("Memory protection setup completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(setup())
