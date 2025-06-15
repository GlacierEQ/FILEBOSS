#!/usr/bin/env python3
"""
Memory Protection Setup - Configure memory protection for DeepSeek-Coder
"""
import os
import sys
import json
import logging
import argparse
import traceback
from pathlib import Path

# Import memory manager
from .memory_manager import get_memory_manager, setup_memory_protection
from .config_manager import ConfigManager

logger = logging.getLogger("DeepSoul-MemoryProtection")

def configure_memory_protection(config: dict = None, debug: bool = False) -> None:
    """
    Configure memory protection based on configuration
    
    Args:
        config: Configuration dictionary
        debug: Whether to enable debug logging
    """
    # Load config using ConfigManager
    default_config = {
        "memory_protection": {
            "enabled": True,
            "ram_warning_threshold": 85,
            "ram_critical_threshold": 95,
            "gpu_warning_threshold": 85,
            "gpu_critical_threshold": 92,
            "check_interval": 3.0,
            "memory_dump_enabled": True,
            "auto_offload_to_cpu": True,
            "aggressive_gc": True
        }
    }
    config_manager = ConfigManager(default_config=default_config)
    config = config_manager.get_all()
    
    # Check if memory protection is enabled
    if not config.get("memory_protection", {}).get("enabled", True):
        logger.info("Memory protection disabled in configuration")
        return
    
    # Get memory protection settings
    memory_protection = config.get("memory_protection", {})
    
    # Configure memory manager
    memory_manager = get_memory_manager()
    memory_manager.ram_warning_threshold = memory_protection.get("ram_warning_threshold", 85) / 100.0
    memory_manager.ram_critical_threshold = memory_protection.get("ram_critical_threshold", 95) / 100.0
    memory_manager.gpu_warning_threshold = memory_protection.get("gpu_warning_threshold", 85) / 100.0
    memory_manager.gpu_critical_threshold = memory_protection.get("gpu_critical_threshold", 92) / 100.0
    memory_manager.check_interval = memory_protection.get("check_interval", 5.0)
    memory_manager.memory_dump_enabled = memory_protection.get("memory_dump_enabled", True)
    
    # Define warning and critical hook functions
    def warning_hook(data):
        """Handle memory warning events"""
        if "ram_usage" in data:
            logger.warning(f"RAM usage warning: {data['ram_usage']*100:.1f}%")
        elif "gpu_usage" in data:
            logger.warning(f"GPU memory warning: {data['gpu_usage']*100:.1f}% (device {data.get('gpu_id', 0)})")
    
    def critical_hook(data):
        """Handle critical memory events"""
        if "ram_usage" in data:
            logger.critical(f"CRITICAL RAM usage: {data['ram_usage']*100:.1f}%")
            
            # Create memory dump
            memory_manager.memory_dump("critical_ram")
            
            # Force garbage collection
            import gc
            gc.collect()
            
        elif "gpu_usage" in data:
            logger.critical(f"CRITICAL GPU memory: {data['gpu_usage']*100:.1f}% (device {data.get('gpu_id', 0)})")
            
            # Create memory dump
            memory_manager.memory_dump("critical_gpu")
            
            # Force CUDA cache clear
            if "torch.cuda" in sys.modules:
                import torch
                torch.cuda.empty_cache()
    
    # Set up memory protection
    setup_memory_protection(warning_hook, critical_hook)
    memory_manager.start_monitoring()
    
    logger.info(f"Memory protection configured and monitoring started")
    
    # Configure auto offload if enabled
    if memory_protection.get("auto_offload_to_cpu", True):
        try:
            from .auto_offload import setup_auto_offload
            # Configure auto offload threshold
            threshold = memory_protection.get("gpu_warning_threshold", 85) / 100.0
            setup_auto_offload(threshold=threshold)
            logger.info(f"Automatic parameter offloading configured (threshold: {threshold:.0%})")
        except Exception as e:
            logger.error(f"Error configuring automatic offloading: {e}")

def generate_default_config(output_path: str = "memory_config.json") -> None:
    """
    Generate default memory configuration file
    
    Args:
        output_path: Path to write configuration file
    """
    # Default configuration
    default_config = {
        "memory_protection": {
            "enabled": True,
            "ram_warning_threshold": 85,
            "ram_critical_threshold": 95,
            "gpu_warning_threshold": 85,
            "gpu_critical_threshold": 92,
            "check_interval": 3.0,
            "memory_dump_enabled": True,
            "memory_dump_dir": "memory_dumps",
            "auto_offload_to_cpu": True,
            "aggressive_gc": True
        },
        "system_specs": {
            "total_ram_gb": 16.0,
            "available_ram_gb": 8.0,
            "cuda_available": True,
            "gpu_count": 1,
        },
        "gpus": [
            {
                "id": 0,
                "name": "NVIDIA GeForce RTX 3080",
                "total_memory_gb": 10.0,
                "warning_threshold": 85,
                "critical_threshold": 92,
                "monitoring_enabled": True
            }
        ],
        "model_specific": {
            "deepseek-coder-1.3b-instruct": {
                "max_batch_size": 16,
                "half_precision": True,
                "use_flash_attention": True,
                "offload_layers": False
            },
            "deepseek-coder-6.7b-instruct": {
                "max_batch_size": 4,
                "half_precision": True,
                "use_flash_attention": True,
                "offload_layers": True,
                "offload_layer_indices": [0, 1, 2, 3, 4, 5]
            }
        },
        "experimental": {
            "use_cpu_offload": True,
            "use_disk_offload": False,
            "use_8bit_quantization": False,
            "use_4bit_quantization": False
        }
    }
    
    # Update with actual system information if possible
    try:
        import torch
        import psutil
        
        # Update RAM info
        mem = psutil.virtual_memory()
        default_config["system_specs"]["total_ram_gb"] = mem.total / (1024**3)
        default_config["system_specs"]["available_ram_gb"] = mem.available / (1024**3)
        
        # Update CUDA info
        default_config["system_specs"]["cuda_available"] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            default_config["system_specs"]["gpu_count"] = torch.cuda.device_count()
            
            # Update GPU info
            default_config["gpus"] = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                default_config["gpus"].append({
                    "id": i,
                    "name": props.name,
                    "total_memory_gb": props.total_memory / (1024**3),
                    "warning_threshold": 85,
                    "critical_threshold": 92,
                    "monitoring_enabled": True
                })
    except Exception as e:
        logger.warning(f"Could not gather system information: {e}")
    
    # Write configuration to file
    try:
        # Create parent directory if needed
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        logger.info(f"Generated default memory configuration at {output_path}")
    except Exception as e:
        logger.error(f"Error writing configuration file: {e}")
        return None
    
    return output_path

def main():
    """Command-line interface for memory protection setup"""
    parser = argparse.ArgumentParser(description="Configure memory protection for DeepSeek-Coder")
    parser.add_argument("--config", help="Path to memory configuration file")
    parser.add_argument("--generate-config", help="Generate default configuration file", action="store_true")
    parser.add_argument("--output", help="Output path for generated configuration", default="memory_config.json")
    parser.add_argument("--debug", help="Enable debug logging", action="store_true")
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    try:
        if args.generate_config:
            # Generate configuration file
            config_path = generate_default_config(args.output)
            if config_path:
                print(f"Generated default configuration at {config_path}")
                sys.exit(0)
            else:
                print("Error generating configuration file")
                sys.exit(1)
        else:
            # Configure memory protection
            config = load_memory_config(args.config)
            configure_memory_protection(config, args.debug)
            print("Memory protection configured successfully")
    except Exception as e:
        logger.error(f"Error in memory protection setup: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
