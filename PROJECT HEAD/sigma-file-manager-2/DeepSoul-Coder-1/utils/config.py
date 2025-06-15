"""
Configuration manager for DeepSeek-Coder.
Handles loading and validating configuration from environment variables.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union, Set, cast
from pathlib import Path
from dataclasses import dataclass, field, asdict

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DeepSeekConfig:
    """Configuration settings for DeepSeek-Coder."""
    
    # Model settings
    model_size: str = "base"  # base, large
    model_path: str = ""
    quantization: str = "none"  # none, int8, fp16, bf16
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    workers: int = 1
    
    # Security settings
    enable_auth: bool = False
    api_keys: List[str] = field(default_factory=list)
    rate_limit: int = 100
    
    # CORS settings
    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = False
    allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "OPTIONS"])
    allow_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    
    # Directory settings
    data_dir: str = "data"
    log_dir: str = "logs"
    cache_dir: str = "cache"
    
    # Performance settings
    torch_compile: bool = True
    flash_attention: bool = True
    max_batch_size: int = 4
    max_concurrent_requests: int = 4
    request_timeout: int = 300
    
    # Elasticsearch settings
    elasticsearch_host: str = "elasticsearch"
    elasticsearch_port: int = 9200
    elasticsearch_index_prefix: str = "deepseek-"
    
    # Monitoring settings
    enable_metrics: bool = True
    enable_telemetry: bool = True
    prometheus_port: int = 9090
    
    # GPU settings
    cuda_visible_devices: str = "all"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_env(cls) -> 'DeepSeekConfig':
        """Load configuration from environment variables."""
        config = cls()
        
        # Model settings
        config.model_size = os.environ.get("MODEL_SIZE", config.model_size)
        config.model_path = os.environ.get("MODEL_PATH", config.model_path)
        config.quantization = os.environ.get("QUANTIZATION_TYPE", config.quantization)
        
        # Server settings
        config.host = os.environ.get("HOST", config.host)
        config.port = int(os.environ.get("PORT", str(config.port)))
        config.log_level = os.environ.get("LOG_LEVEL", config.log_level)
        config.workers = int(os.environ.get("WORKERS", str(config.workers)))
        
        # Security settings
        config.enable_auth = os.environ.get("ENABLE_AUTH", "").lower() == "true"
        
        api_keys_str = os.environ.get("API_KEYS", "")
        if api_keys_str:
            config.api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        
        config.rate_limit = int(os.environ.get("RATE_LIMIT", str(config.rate_limit)))
        
        # CORS settings
        origins_str = os.environ.get("ALLOW_ORIGINS", "*")
        if origins_str != "*":
            config.allow_origins = [o.strip() for o in origins_str.split(",") if o.strip()]
        
        config.allow_credentials = os.environ.get("ALLOW_CREDENTIALS", "").lower() == "true"
        
        methods_str = os.environ.get("ALLOW_METHODS", "")
        if methods_str:
            config.allow_methods = [m.strip() for m in methods_str.split(",") if m.strip()]
        
        headers_str = os.environ.get("ALLOW_HEADERS", "")
        if headers_str:
            config.allow_headers = [h.strip() for h in headers_str.split(",") if h.strip()]
        
        # Directory settings
        config.data_dir = os.environ.get("DATA_DIR", config.data_dir)
        config.log_dir = os.environ.get("LOG_DIR", config.log_dir)
        config.cache_dir = os.environ.get("CACHE_DIR", config.cache_dir)
        
        # Performance settings
        config.torch_compile = os.environ.get("TORCH_COMPILE", "").lower() == "1" or os.environ.get("TORCH_COMPILE", "").lower() == "true"
        config.flash_attention = os.environ.get("FLASH_ATTENTION", "").lower() != "false"
        config.max_batch_size = int(os.environ.get("MAX_BATCH_SIZE", str(config.max_batch_size)))
        config.max_concurrent_requests = int(os.environ.get("MAX_CONCURRENT_REQUESTS", str(config.max_concurrent_requests)))
        config.request_timeout = int(os.environ.get("REQUEST_TIMEOUT", str(config.request_timeout)))
        
        # Elasticsearch settings
        config.elasticsearch_host = os.environ.get("ELASTICSEARCH_HOST", config.elasticsearch_host)
        config.elasticsearch_port = int(os.environ.get("ELASTICSEARCH_PORT", str(config.elasticsearch_port)))
        config.elasticsearch_index_prefix = os.environ.get("ELASTICSEARCH_INDEX_PREFIX", config.elasticsearch_index_prefix)
        
        # Monitoring settings
        config.enable_metrics = os.environ.get("ENABLE_METRICS", "").lower() != "false"
        config.enable_telemetry = os.environ.get("ENABLE_TELEMETRY", "").lower() != "false"
        config.prometheus_port = int(os.environ.get("PROMETHEUS_PORT", str(config.prometheus_port)))
        
        # GPU settings
        config.cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", config.cuda_visible_devices)
        
        return config
    
    def validate(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        # Model size validation
        if self.model_size not in ["base", "large", "instruct"]:
            errors.append(f"Invalid model size: {self.model_size}. Must be one of: base, large, instruct")
        
        # Port validation
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid port: {self.port}. Must be between 1 and 65535")
        
        # Log level validation
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"Invalid log level: {self.log_level}")
        
        # Directory validation
        for dir_name, dir_path in [("data_dir", self.data_dir), 
                                  ("log_dir", self.log_dir), 
                                  ("cache_dir", self.cache_dir)]:
            if dir_path and not os.path.exists(dir_path):
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {dir_path}")
                except Exception as e:
                    errors.append(f"Could not create {dir_name} directory ({dir_path}): {str(e)}")
        
        return errors
    
    def setup_environment(self):
        """Set up environment variables based on the configuration."""
        # Set CUDA device if specified
        if self.cuda_visible_devices != "all":
            os.environ["CUDA_VISIBLE_DEVICES"] = self.cuda_visible_devices
        
        # Set PyTorch memory allocation options
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"
        
        # Set up Flash Attention if enabled
        if self.flash_attention:
            os.environ["TRANSFORMERS_ATTENTION_IMPLEMENTATION"] = "flash_attention_2"


# Global configuration instance
_config = None

def get_config() -> DeepSeekConfig:
    """
    Get the global configuration instance.
    
    Returns:
        Global DeepSeekConfig instance
    """
    global _config
    if _config is None:
        _config = DeepSeekConfig.from_env()
    return _config

def reload_config() -> DeepSeekConfig:
    """
    Reload the configuration from environment variables.
    
    Returns:
        Updated DeepSeekConfig instance
    """
    global _config
    _config = DeepSeekConfig.from_env()
    return _config
