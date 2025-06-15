"""
Centralized configuration management for Sorting Hat

This module provides a unified way to access configuration settings
from environment variables, config files, and default values.
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Base directory for the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default safe path for file operations
DEFAULT_SAFE_PATH = os.path.join(os.path.expanduser("~"), "OrganizeFolder")

# Default configuration values
DEFAULT_CONFIG = {
    "paths": {
        "safe_path": DEFAULT_SAFE_PATH,
        "data_dir": os.path.join(BASE_DIR, "data"),
        "logs_dir": os.path.join(BASE_DIR, "logs"),
        "cache_dir": os.path.join(BASE_DIR, "cache"),
    },
    "api": {
        "groq_api_key": "",
        "agentops_api_key": "",
    },
    "file_watching": {
        "recursive": True,
        "ignore_patterns": [
            ".*",  # Hidden files
            "*/.git/*",  # Git repositories
            "*/node_modules/*",  # Node modules
            "*/venv/*",  # Python virtual environments
            "~$*",  # Temporary files
            "*.tmp",  # Temporary files
        ],
        "depth": 1,  # Default depth for file watching
    },
    "system": {
        "debug": False,
        "log_level": "INFO",
        "incognito_mode": False,  # Whether to use local models instead of cloud APIs
    },
    "categories": [
        {
            "name": "Legal",
            "pattern": r"\b(court|lawsuit|legal|attorney|lawyer|filing|evidence|custody|visitation|restraining|appeal)\b",
            "extensions": [".pdf", ".doc", ".docx", ".txt"]
        },
        {
            "name": "Financial",
            "pattern": r"\b(tax|bank|statement|bill|receipt|invest|retirement|credit|insurance|loan|debt|expense|budget)\b",
            "extensions": [".pdf", ".xls", ".xlsx", ".csv"]
        },
        {
            "name": "Real Estate",
            "pattern": r"\b(mortgage|rent|home|inspection|repair|maintenance|utility|property|moving|storage|house|apartment)\b",
            "extensions": [".pdf", ".doc", ".docx", ".jpg", ".png"]
        },
        {
            "name": "Family",
            "pattern": r"\b(parenting|visitation|school|medical|doctor|fitness|diet|travel|family|contact|history|health)\b",
            "extensions": [".pdf", ".doc", ".docx", ".jpg", ".png"]
        },
        {
            "name": "Business",
            "pattern": r"\b(client|contract|agreement|invoice|payment|marketing|branding|business|compliance|plan|hr|network)\b",
            "extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]
        },
        {
            "name": "Education",
            "pattern": r"\b(course|certificate|study|note|research|paper|ebook|ai|programming|development|learn|class|school)\b",
            "extensions": [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt"]
        },
        {
            "name": "Creativity",
            "pattern": r"\b(photo|video|music|graphic|design|writing|draft|screenplay|project|creative|art|drawing)\b",
            "extensions": [".jpg", ".png", ".gif", ".mp4", ".mp3", ".wav", ".psd", ".ai", ".indd", ".svg"]
        },
        {
            "name": "Technology",
            "pattern": r"\b(code|project|github|software|tool|script|automation|troubleshoot|hardware|cloud|backup|tech)\b",
            "extensions": [".js", ".py", ".html", ".css", ".cpp", ".java", ".php", ".json", ".xml", ".log"]
        },
        {
            "name": "Miscellaneous",
            "pattern": r".*",
            "extensions": ["*"]
        }
    ],
    "ignore_folders": [
        "My Music",
        "My Pictures",
        "My Videos",
        "Start Menu",
        "Templates",
        "NetHood",
        "PrintHood",
        "Recent",
        "SendTo",
        "Application Data",
        "Local Settings",
        "Cookies",
        "History",
        "Temporary Internet Files"
    ],
}

class Config:
    """Configuration manager for Sorting Hat"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration if not already initialized"""
        if self._initialized:
            return
            
        self._config = DEFAULT_CONFIG.copy()
        self._load_config_file()
        self._load_env_variables()
        self._ensure_directories()
        self._initialized = True
        
    def _load_config_file(self):
        """Load configuration from config.json if it exists"""
        config_path = os.path.join(BASE_DIR, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self._update_nested_dict(self._config, file_config)
            except Exception as e:
                logging.error(f"Error loading config file: {e}")
    
    def _load_env_variables(self):
        """Load configuration from environment variables"""
        # API keys
        if os.environ.get("GROQ_API_KEY"):
            self._config["api"]["groq_api_key"] = os.environ.get("GROQ_API_KEY")
            
        if os.environ.get("AGENTOPS_API_KEY"):
            self._config["api"]["agentops_api_key"] = os.environ.get("AGENTOPS_API_KEY")
            
        # System settings
        if os.environ.get("DEBUG"):
            self._config["system"]["debug"] = os.environ.get("DEBUG").lower() in ("true", "1", "yes")
            
        if os.environ.get("LOG_LEVEL"):
            self._config["system"]["log_level"] = os.environ.get("LOG_LEVEL")
            
        if os.environ.get("INCOGNITO_MODE"):
            self._config["system"]["incognito_mode"] = os.environ.get("INCOGNITO_MODE").lower() in ("true", "1", "yes")
            
        # Paths
        if os.environ.get("SAFE_PATH"):
            self._config["paths"]["safe_path"] = os.environ.get("SAFE_PATH")
    
    def _update_nested_dict(self, d: Dict, u: Dict) -> Dict:
        """Recursively update a nested dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def _ensure_directories(self):
        """Ensure that required directories exist"""
        for dir_name, dir_path in self._config["paths"].items():
            os.makedirs(dir_path, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using a dot-notation path
        
        Args:
            key_path: Dot-notation path to the config value (e.g., "paths.safe_path")
            default: Default value to return if the key doesn't exist
            
        Returns:
            The configuration value or the default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using a dot-notation path
        
        Args:
            key_path: Dot-notation path to the config value (e.g., "paths.safe_path")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
            
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save the current configuration to config.json"""
        config_path = os.path.join(BASE_DIR, "config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config file: {e}")
    
    def get_all(self) -> Dict:
        """Get the entire configuration dictionary"""
        return self._config.copy()

# Create a singleton instance
config = Config()

# Helper functions for common config operations
def get_safe_path() -> str:
    """Get the safe path for file operations"""
    return config.get("paths.safe_path")

def get_api_key(provider: str) -> Optional[str]:
    """Get an API key for a specific provider"""
    return config.get(f"api.{provider}_api_key")

def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return config.get("system.debug", False)

def get_log_level() -> str:
    """Get the configured log level"""
    return config.get("system.log_level", "INFO")

def is_incognito_mode() -> bool:
    """Check if incognito mode is enabled (use local models)"""
    return config.get("system.incognito_mode", False)

def get_categories() -> list:
    """Get the configured file categories"""
    return config.get("categories", [])

def get_ignore_folders() -> list:
    """Get the list of folders to ignore"""
    return config.get("ignore_folders", [])
