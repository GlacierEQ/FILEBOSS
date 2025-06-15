"""Configuration management for LawGlance."""
import os
import json
from typing import Dict, Any, Optional, Union
import logging
from pathlib import Path

logger = logging.getLogger("lawglance.config")

class ConfigManager:
    """Manages configuration settings for the application."""
    
    def __init__(self, config_dir: Optional[str] = None, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store config files (default: ~/.lawglance)
            config_file: Name of config file (default: config.json)
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".lawglance"
        self.config_file = config_file or "config.json"
        self.config_path = self.config_dir / self.config_file
        self.config: Dict[str, Any] = {}
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing config if available
        self.load_config()
    
    def __repr__(self) -> str:
        """Return string representation of config manager."""
        return f"ConfigManager(config_path={self.config_path})"
    
    def load_config(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if config was loaded successfully, False otherwise
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
                logger.info(f"Loaded config from {self.config_path}")
                return True
            else:
                logger.info(f"Config file {self.config_path} not found. Using default config.")
                self.config = {}
                return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = {}
            return False
    
    def save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if config was saved successfully, False otherwise
        """
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved config to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
    
    def update(self, settings: Dict[str, Any]) -> None:
        """
        Update configuration with multiple values.
        
        Args:
            settings: Dictionary of configuration key-value pairs
        """
        self.config.update(settings)
    
    def reset(self) -> None:
        """Reset configuration to empty state."""
        self.config = {}
        self.save_config()
