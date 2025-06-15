"""
Configuration Manager - Centralized configuration loading, saving, and access
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("DeepSoul-ConfigManager")

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_dir: str = "deepsoul_config", default_config: Dict[str, Any] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_dir: Directory containing configuration files
            default_config: Default configuration dictionary
        """
        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / "system_config.json"
        self.default_config = default_config or {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        # Create config directory if needed
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config from file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                
                # Merge with default config
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                logger.error(f"Error loading configuration from {self.config_path}: {str(e)}")
        
        # Create default config if it doesn't exist
        logger.info("Creating default configuration")
        self._save_config(self.default_config)
        return self.default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_path}: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.config[key] = value
        self._save_config(self.config)
    
    def update(self, new_config: Dict[str, Any]) -> None:
        """Update multiple configuration values"""
        self.config.update(new_config)
        self._save_config(self.config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a default configuration
    default_config = {
        "model_name": "default_model",
        "api_key": "default_api_key"
    }
    
    # Create a config manager
    config_manager = ConfigManager(default_config=default_config)
    
    # Get a value
    model_name = config_manager.get("model_name")
    print(f"Model name: {model_name}")
    
    # Set a value
    config_manager.set("model_name", "new_model")
    print(f"Updated model name: {config_manager.get('model_name')}")
    
    # Update multiple values
    config_manager.update({
        "model_name": "another_model",
        "api_key": "new_api_key"
    })
    print(f"All config: {config_manager.get_all()}")
