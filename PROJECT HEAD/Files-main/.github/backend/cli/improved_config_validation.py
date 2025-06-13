"""
Improved configuration validation for CodexFlō CLI
"""
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Configuration validation error"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"

def validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> Path:
    """Validate and sanitize file paths with security checks"""
    try:
        # Convert to Path and resolve
        path_obj = Path(path).expanduser().resolve()
        
        # Basic security check - ensure we're not going outside reasonable bounds
        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")
        
        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")
        
        return path_obj
    except Exception as e:
        raise ValidationError(f"Invalid path '{path}': {e}")

def validate_config_schema(config: Dict[str, Any]) -> List[str]:
    """Validate configuration structure and required fields"""
    errors = []
    
    # Required top-level sections
    required_sections = ["app", "ai", "storage", "modules"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # AI configuration validation
    if "ai" in config:
        ai_config = config["ai"]
        provider = ai_config.get("provider")
        
        if provider not in [p.value for p in AIProvider]:
            errors.append(f"Invalid AI provider: {provider}")
        
        # Check for API key if using cloud providers
        if provider in ["openai", "anthropic", "gemini"]:
            api_key = ai_config.get("api_key")
            if not api_key or api_key.startswith("${"):
                errors.append(f"API key required for {provider} provider")
        
        # Validate model parameters
        temp = ai_config.get("temperature", 0.1)
        if not 0 <= temp <= 2:
            errors.append("Temperature must be between 0 and 2")
    
    # Storage validation
    if "storage" in config:
        storage_config = config["storage"]
        base_path = storage_config.get("base_path")
        if base_path:
            try:
                validate_path(base_path)
            except ValidationError as e:
                errors.append(f"Storage path error: {e}")
    
    return errors

def load_and_validate_config(config_path: str) -> Dict[str, Any]:
    """Load and validate configuration file with error handling"""
    try:
        path_obj = validate_path(config_path, must_exist=True)
        
        with open(path_obj, 'r') as f:
            if path_obj.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif path_obj.suffix == '.json':
                config = json.load(f)
            else:
                raise ConfigError(f"Unsupported config file format: {path_obj.suffix}")
        
        errors = validate_config_schema(config)
        if errors:
            error_msg = "\n".join([f"- {error}" for error in errors])
            raise ConfigError(f"Configuration validation failed:\n{error_msg}")
        
        return config
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {config_path}")
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ConfigError(f"Error parsing config file: {e}")
    except Exception as e:
        logger.exception("Config validation error")
        raise ConfigError(f"Unexpected error validating config: {e}")

# Example usage:
# try:
#     config = load_and_validate_config("config/ai_file_explorer.yml")
#     print("Config is valid!")
# except ConfigError as e:
#     print(f"Config error: {e}")