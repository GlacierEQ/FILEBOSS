"""
Model Loader - Utility for loading models with appropriate configurations
"""
import os
import gc
import json
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM

from .memory_manager import get_memory_manager
from .auto_offload import get_auto_offload

logger = logging.getLogger("DeepSoul-ModelLoader")

class ModelLoader:
    """
    Utility for loading models with appropriate configurations
    
    This class handles loading transformer models with optimized settings
    based on the device capabilities and memory constraints.
    """
    
    def __init__(self, 
               config_dir: Optional[str] = None,
               cache_dir: Optional[str] = None):
        """
        Initialize the model loader
        
        Args:
            config_dir: Directory containing model configuration files
            cache_dir: Directory to cache downloaded models
        """
        self.memory_manager = get_memory_manager()
        self.auto_offload = get_auto_offload()
        
        # Set up configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent / "deepsoul_config" / "models"
        
        # Set up cache directory
        self.cache_dir = cache_dir
        
        # Load model configurations
        self.model_configs = self._load_model_configs()
        
        # Device capabilities
        self.device_capabilities = self._detect_device_capabilities()
    
    def _load_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load model configuration files
        
        Returns:
            Dictionary mapping model names to configurations
        """
        configs = {}
        
        # Ensure config directory exists
        if not self.config_dir.exists():
            logger.warning(f"Model config directory does not exist: {self.config_dir}")
            return configs
        
        # Load all JSON files in the config directory
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    
                # Get model name from config
                model_name = config.get("model_name")
                if model_name:
                    configs[model_name] = config
                    logger.debug(f"Loaded configuration for model: {model_name}")
            except Exception as e:
                logger.error(f"Error loading model config from {config_file}: {str(e)}")
        
        logger.info(f"Loaded {len(configs)} model configurations")
        return configs
    
    def _detect_device_capabilities(self) -> Dict[str, Any]:
        """
        Detect the capabilities of the current device
        
        Returns:
            Dictionary with device capability information
        """
        capabilities = {
            "cuda_available": torch.cuda.is_available(),
            "device_count": 0,
            "devices": [],
            "cpu_count": os.cpu_count() or 1,
            "system_memory_gb": psutil.virtual_memory().total / (1024**3)
        }
        
        if capabilities["cuda_available"]:
            capabilities["device_count"] = torch.cuda.device_count()
            
            # Get information for each CUDA device
            for i in range(capabilities["device_count"]):
                device_props = torch.cuda.get_device_properties(i)
                device_info = {
                    "name": device_props.name,
                    "total_memory_gb": device_props.total_memory / (1024**3),
                    "compute_capability": f"{device_props.major}.{device_props.minor}",
                    "multi_processor_count": device_props.multi_processor_count
                }
                capabilities["devices"].append(device_info)
        
        logger.info(f"Device capabilities: {capabilities['cuda_available']=}, "
                   f"{capabilities['device_count']=}, "
                   f"{capabilities['system_memory_gb']:.1f} GB RAM")
        
        return capabilities
    
    def load_model(self, model_name: str, low_memory: bool = False) -> Tuple[Any, Any]:
        """
        Load a model with appropriate configuration
        
        Args:
            model_name: Name or path of the model to load
            low_memory: Whether to use memory-saving techniques
            
        Returns:
            Tuple of (model, tokenizer)
        """
        logger.info(f"Loading model: {model_name}")
        
        # Check if we have a specific config for this model
        config = self.model_configs.get(model_name, {})
        
        # Determine target device
        device = self._determine_target_device(model_name, config)
        
        # Set up loading parameters
        loading_params = self._prepare_loading_params(model_name, config, low_memory, device)
        
        # Load tokenizer
        tokenizer = self._load_tokenizer(model_name, loading_params)
        
        # Load model
        model = self._load_model_with_fallbacks(model_name, loading_params, device, low_memory)
        
        return model, tokenizer
    
    def _determine_target_device(self, model_name: str, config: Dict[str, Any]) -> torch.device:
        """
        Determine the best target device for the model
        
        Args:
            model_name: Model name
            config: Model configuration
            
        Returns:
            Target device
        """
        # If CUDA is not available, default to CPU
        if not self.device_capabilities["cuda_available"]:
            return torch.device("cpu")
        
        # Get memory requirements
        required_vram_mb = config.get("requirements", {}).get("min_vram_mb", 0)
        
        # Check if we have sufficient GPU memory
        if required_vram_mb > 0:
            # Find best device with sufficient memory
            for i, device_info in enumerate(self.device_capabilities["devices"]):
                available_memory = device_info["total_memory_gb"] * 1024  # Convert to MB
                if available_memory >= required_vram_mb:
                    return torch.device(f"cuda:{i}")
        
        # Default to first CUDA device if we couldn't determine requirements
        return torch.device("cuda:0")
    
    def _prepare_loading_params(self, model_name: str, config: Dict[str, Any], 
                              low_memory: bool, device: torch.device) -> Dict[str, Any]:
        """
        Prepare parameters for loading the model
        
        Args:
            model_name: Model name
            config: Model configuration
            low_memory: Whether to use memory-saving techniques
            device: Target device
            
        Returns:
            Dictionary with loading parameters
        """
        params = {
            "cache_dir": self.cache_dir,
            "torch_dtype": torch.float32,
            "device_map": None
        }
        
        # Set quantization parameters if needed
        if low_memory or config.get("quantization", "none") != "none":
            # Don't set torch_dtype when using quantization
            pass
        elif device.type == "cuda" and config.get("optimization", {}).get("half_precision", True):
            # Use FP16 for CUDA devices if supported
            params["torch_dtype"] = torch.float16
        
        # Check for device mapping
        multi_gpu = config.get("requirements", {}).get("multi_gpu", False)
        if multi_gpu and self.device_capabilities["device_count"] > 1:
            params["device_map"] = "auto"
        elif device.type == "cuda":
            params["device_map"] = {"": device.index}
        
        # Add load in 4-bit parameters if needed
        if low_memory and "quantization_options" in config and config["quantization_options"].get("supports_4bit", False):
            bnb_config = transformers.BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
            params["quantization_config"] = bnb_config
        # Add load in 8-bit parameters if needed
        elif low_memory and "quantization_options" in config and config["quantization_options"].get("supports_8bit", False):
            params["load_in_8bit"] = True
        
        return params
    
    def _load_tokenizer(self, model_name: str, params: Dict[str, Any]) -> Any:
        """
        Load tokenizer for the model
        
        Args:
            model_name: Model name
            params: Loading parameters
            
        Returns:
            Loaded tokenizer
        """
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=params.get("cache_dir")
            )
            return tokenizer
        except Exception as e:
            logger.error(f"Error loading tokenizer {model_name}: {e}")
            raise
    
    def _load_model_with_fallbacks(self, model_name: str, params: Dict[str, Any], 
                                 device: torch.device, low_memory: bool) -> Any:
        """
        Load model with fallbacks for error conditions
        
        Args:
            model_name: Model name
            params: Loading parameters
            device: Target device
            low_memory: Whether to use memory-saving techniques
            
        Returns:
            Loaded model
        """
        model = None
        
        # First attempt - try with provided parameters
        try:
            logger.info(f"Loading model {model_name} with params: {params}")
            model = AutoModelForCausalLM.from_pretrained(model_name, **params)
            logger.info(f"Successfully loaded model {model_name}")
            return model
        except Exception as e:
            logger.warning(f"Error loading model with initial params: {e}")
            # Continue to fallbacks
        
        # Second attempt - try without device_map
        try:
            fallback_params = params.copy()
            if "device_map" in fallback_params:
                del fallback_params["device_map"]
                
            logger.info(f"Trying to load model without device_map")
            model = AutoModelForCausalLM.from_pretrained(model_name, **fallback_params)
            
            # Move model to device after loading
            if device.type == "cuda":
                model = model.to(device)
                
            logger.info(f"Successfully loaded model {model_name}")
            return model
        except Exception as e:
            logger.warning(f"Error loading model without device_map: {e}")
            # Continue to fallbacks
        
        # Third attempt - try with CPU first, then move to GPU
        try:
            logger.info("Trying to load model on CPU first")
            cpu_params = {k: v for k, v in params.items() if k != "device_map"}
            
            # Force garbage collection before loading
            gc.collect()
            torch.cuda.empty_cache()
            
            model = AutoModelForCausalLM.from_pretrained(model_name, **cpu_params)
            
            # If low memory mode, use auto offload
            if low_memory and device.type == "cuda":
                logger.info("Using layer offloading for low memory mode")
                self.auto_offload.offload_parameters(model)
            elif device.type == "cuda":
                logger.info(f"Moving model to {device}")
                model = model.to(device)
            
            logger.info(f"Successfully loaded model {model_name}")
            return model
        except Exception as e:
            logger.error(f"All attempts to load model failed: {e}")
            raise
    
    def is_model_compatible(self, model_name: str) -> bool:
        """
        Check if a model is compatible with the current device
        
        Args:
            model_name: Model name
            
        Returns:
            Whether the model is compatible
        """
        # Get model config if available
        config = self.model_configs.get(model_name, {})
        
        # If no config, we assume it's compatible
        if not config:
            return True
        
        # Check memory requirements
        required_vram_mb = config.get("requirements", {}).get("min_vram_mb", 0)
        required_ram_gb = config.get("requirements", {}).get("min_ram_gb", 0)
        
        # Check system RAM
        if required_ram_gb > 0:
            if self.device_capabilities["system_memory_gb"] < required_ram_gb:
                logger.warning(f"Insufficient RAM for model {model_name}: "
                           f"Required {required_ram_gb} GB, Available {self.device_capabilities['system_memory_gb']:.1f} GB")
                return False
        
        # Check GPU memory if CUDA is available and required
        if required_vram_mb > 0 and self.device_capabilities["cuda_available"]:
            # Check if any device has sufficient memory
            sufficient_memory = False
            for device_info in self.device_capabilities["devices"]:
                available_memory = device_info["total_memory_gb"] * 1024  # Convert to MB
                if available_memory >= required_vram_mb:
                    sufficient_memory = True
                    break
            
            if not sufficient_memory:
                logger.warning(f"Insufficient GPU memory for model {model_name}: "
                           f"Required {required_vram_mb} MB")
                return False
        
        return True
    
    def get_compatible_models(self) -> List[str]:
        """
        Get list of models compatible with the current device
        
        Returns:
            List of compatible model names
        """
        compatible_models = []
        
        for model_name in self.model_configs:
            if self.is_model_compatible(model_name):
                compatible_models.append(model_name)
        
        return compatible_models
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a model
        
        Args:
            model_name: Model name
            
        Returns:
            Dictionary with model information
        """
        return self.model_configs.get(model_name, {})
    
    def unload_model(self, model) -> None:
        """
        Unload a model to free memory
        
        Args:
            model: Model to unload
        """
        try:
            # Move model to CPU first
            if hasattr(model, "to") and callable(model.to):
                model.to("cpu")
            
            # Delete model
            del model
            
            # Force garbage collection
            gc.collect()
            torch.cuda.empty_cache()
            
            logger.info("Unloaded model")
        except Exception as e:
            logger.error(f"Error unloading model: {e}")


# Global instance for easy access
_model_loader = None

def get_model_loader() -> ModelLoader:
    """
    Get the global model loader instance
    
    Returns:
        ModelLoader instance
    """
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader

def load_model(model_name: str, low_memory: bool = False) -> Tuple[Any, Any]:
    """
    Load a model using the global model loader
    
    Args:
        model_name: Model name
        low_memory: Whether to use memory-saving techniques
        
    Returns:
        Tuple of (model, tokenizer)
    """
    loader = get_model_loader()
    return loader.load_model(model_name, low_memory)
