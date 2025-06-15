"""
Configuration management for Lawglance system.
Centralizes all configurable parameters and provides loading/saving functionality.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    "models": {
        "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
        "qa_model": "deepset/roberta-base-squad2",
        "llm": "google/flan-t5-base",
        "semantic_analyzer": "nlpaueb/legal-bert-base-uncased"
    },
    "api_keys": {
        "huggingface_token": "YOUR_TOKEN_HERE"
    },
    "retrieval": {
        "k": 10,
        "score_threshold": 0.75
    },
    "document_processing": {
        "chunk_size": 512,
        "chunk_overlap": 100,
        "max_document_size": 10000000  # ~10MB
    },
    "caching": {
        "enabled": True,
        "max_cache_size": 100,  # Number of documents to cache
        "cache_dir": ".cache"
    },
    "state": {
        "save_interval": 3,  # Save state every N steps
        "state_file": "ai_state.json",
        "backup_file": "ai_state_prev.json"
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "lawglance.log"
    }
}

class Config:
    """Configuration management class for Lawglance."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from file or defaults.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or os.environ.get("LAWGLANCE_CONFIG") or "lawglance_config.json"
        self.config = DEFAULT_CONFIG.copy()
        self.load()
        
        # Set up logging based on config
        logging_config = self.config["logging"]
        logging.basicConfig(
            level=getattr(logging, logging_config["level"]),
            format=logging_config["format"],
            filename=logging_config["file"]
        )
        self.logger = logging.getLogger("lawglance.config")
        
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """Get configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key within section (optional)
            
        Returns:
            Configuration value
        """
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key)
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key within section
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Loaded configuration
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    loaded_config = json.load(f)
                
                # Update default config with loaded values
                for section, values in loaded_config.items():
                    if section in self.config and isinstance(self.config[section], dict):
                        self.config[section].update(values)
                    else:
                        self.config[section] = values
                        
                # Pick up any API token from environment
                if "HUGGINGFACE_API_TOKEN" in os.environ:
                    self.config["api_keys"]["huggingface_token"] = os.environ["HUGGINGFACE_API_TOKEN"]
                
                return self.config
        except Exception as e:
            print(f"Error loading configuration: {e}")
        return self.config
    
    def save(self) -> bool:
        """Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def create_default_config(self, path: Optional[str] = None) -> bool:
        """Create default configuration file.
        
        Args:
            path: Path to save configuration (optional)
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            save_path = path or self.config_path
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            with open(save_path, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            return True
        except Exception as e:
            print(f"Error creating default configuration: {e}")
            return False
