"""
Plugin System - Framework for creating and loading plugins
"""
import os
import sys
import json
import logging
import importlib
import pkgutil
from typing import Dict, List, Any, Set, Optional, Type, Callable

from .component_registry import get_registry, register_component

logger = logging.getLogger("DeepSoul-PluginSystem")

class Plugin:
    """Base class for all DeepSeek-Coder plugins"""
    
    # Class properties
    NAME = "base_plugin"
    VERSION = "0.1.0"
    DESCRIPTION = "Base plugin class"
    AUTHOR = "Unknown"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the plugin
        
        Args:
            config: Plugin configuration
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
    
    def initialize(self) -> bool:
        """
        Initialize the plugin
        
        Returns:
            True if initialization was successful, False otherwise
        """
        return True
    
    def shutdown(self) -> None:
        """Shutdown the plugin"""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information
        
        Returns:
            Dictionary with plugin information
        """
        return {
            "name": self.NAME,
            "version": self.VERSION,
            "description": self.DESCRIPTION,
            "author": self.AUTHOR,
            "enabled": self.enabled
        }

class PluginManager:
    """Manages DeepSeek-Coder plugins"""
    
    def __init__(self, plugin_dirs: List[str] = None):
        """
        Initialize the plugin manager
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or ["plugins"]
        self.plugins: Dict[str, Plugin] = {}
        self.registry = get_registry()
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins
        
        Returns:
            List of discovered plugin names
        """
        discovered = []
        
        # Add plugin directories to path
        original_path = sys.path.copy()
        for plugin_dir in self.plugin_dirs:
            if os.path.isdir(plugin_dir):
                sys.path.insert(0, plugin_dir)
        
        try:
            # Search for plugins in each directory
            for plugin_dir in self.plugin_dirs:
                if not os.path.isdir(plugin_dir):
                    logger.warning(f"Plugin directory not found: {plugin_dir}")
                    continue
                
                for _, name, ispkg in pkgutil.iter_modules([plugin_dir]):
                    if ispkg:
                        # Try to import as a package
                        try:
                            module = importlib.import_module(name)
                            
                            # Look for Plugin subclasses
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and 
                                    issubclass(attr, Plugin) and 
                                    attr is not Plugin):
                                    discovered.append(name)
                                    break
                        except ImportError:
                            logger.warning(f"Error importing plugin: {name}")
        
        finally:
            # Restore original path
            sys.path = original_path
        
        return discovered
    
    def load_plugin(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Plugin]:
        """
        Load a plugin by name
        
        Args:
            name: Plugin name
            config: Optional plugin configuration
            
        Returns:
            Plugin instance or None if loading failed
        """
        if name in self.plugins:
            logger.warning(f"Plugin {name} is already loaded")
            return self.plugins[name]
        
        try:
            # Import the plugin module
            module = importlib.import_module(name)
            
            # Find Plugin subclass
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Plugin) and 
                    attr is not Plugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                logger.error(f"No Plugin subclass found in module {name}")
                return None
            
            # Create plugin instance
            plugin = plugin_class(config)
            
            # Initialize plugin
            if plugin.initialize():
                self.plugins[name] = plugin
                logger.info(f"Loaded plugin: {plugin.NAME} v{plugin.VERSION}")
                return plugin
            else:
                logger.error(f"Failed to initialize plugin: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading plugin {name}: {str(e)}")
            return None
    
    def load_plugins_from_config(self, config: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Load plugins from configuration
        
        Args:
            config: Configuration dictionary mapping plugin names to configurations
            
        Returns:
            List of successfully loaded plugin names
        """
        loaded = []
        
        for name, plugin_config in config.items():
            if plugin_config.get("enabled", True):
                plugin = self.load_plugin(name, plugin_config)
                if plugin is not None:
                    loaded.append(name)
        
        logger.info(f"Loaded {len(loaded)} plugins from configuration")
        return loaded
    
    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        if name not in self.plugins:
            logger.warning(f"Plugin {name} is not loaded")
            return False
        
        try:
            # Shut down the plugin
            self.plugins[name].shutdown()
            
            # Remove from loaded plugins
            del self.plugins[name]
            
            logger.info(f"Unloaded plugin: {name}")
            return True
        except Exception as e:
            logger.error(f"Error unloading plugin {name}: {str(e)}")
            return False
    
    def get_loaded_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about loaded plugins
        
        Returns:
            Dictionary mapping plugin names to information
        """
        return {
            name: plugin.get_info()
            for name, plugin in self.plugins.items()
        }
    
    def shutdown(self) -> None:
        """Shutdown all plugins"""
        for name, plugin in list(self.plugins.items()):
            try:
                plugin.shutdown()
                logger.debug(f"Shut down plugin: {name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {name}: {str(e)}")
        
        self.plugins.clear()

# Global instance
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
