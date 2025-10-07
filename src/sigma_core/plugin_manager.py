"""Plugin Management System for Dynamic Loading"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator
import logging
import traceback

from .event_bus import EventBus

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages dynamic loading and lifecycle of plugins"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.plugins: Dict[str, Any] = {}
        self.plugin_metadata: Dict[str, Dict] = {}
        
        logger.info("🔌 PluginManager initialized")
    
    def discover_plugins(self, plugin_dir: str) -> Generator[str, None, None]:
        """Discover all plugins in the plugins directory"""
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            logger.warning(f"⚠️ Plugin directory not found: {plugin_dir}")
            return
        
        logger.info(f"🔍 Scanning for plugins in: {plugin_path}")
        
        for item in plugin_path.iterdir():
            if item.is_dir():
                # Check for plugin.py file
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    logger.info(f"🔍 Found plugin: {item.name}")
                    yield item.name
                else:
                    # Check for __init__.py with Plugin class
                    init_file = item / "__init__.py"
                    if init_file.exists():
                        logger.info(f"🔍 Found potential plugin package: {item.name}")
                        yield item.name
    
    def load_plugin(self, plugin_name: str, plugin_dir: str = "src/plugins/") -> bool:
        """Dynamically load a single plugin"""
        logger.info(f"🔄 Loading plugin: {plugin_name}")
        
        try:
            # Construct module path
            module_path = f"src.plugins.{plugin_name}"
            
            # Try to import plugin.py first
            plugin_module_path = f"{module_path}.plugin"
            
            try:
                module = importlib.import_module(plugin_module_path)
            except ImportError:
                # Fallback to package __init__.py
                module = importlib.import_module(module_path)
            
            # Look for Plugin class
            if not hasattr(module, 'Plugin'):
                logger.error(f"❌ No 'Plugin' class found in {plugin_name}")
                return False
            
            plugin_class = getattr(module, 'Plugin')
            
            # Instantiate plugin
            plugin_instance = plugin_class()
            
            # Initialize plugin
            if hasattr(plugin_instance, 'initialize'):
                if not plugin_instance.initialize():
                    logger.error(f"❌ Plugin {plugin_name} failed to initialize")
                    return False
            
            # Register plugin
            self.plugins[plugin_name] = plugin_instance
            
            # Store metadata if available
            if hasattr(plugin_instance, 'metadata'):
                self.plugin_metadata[plugin_name] = plugin_instance.metadata
            
            # Register event handlers
            if hasattr(plugin_instance, 'register_events'):
                plugin_instance.register_events(self.event_bus)
            
            logger.info(f"✅ Successfully loaded plugin: {plugin_name}")
            
            # Emit plugin loaded event
            self.event_bus.emit('plugin_loaded', {
                'plugin_name': plugin_name,
                'plugin_instance': plugin_instance
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {plugin_name}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        logger.info(f"📄 Unloading plugin: {plugin_name}")
        
        if plugin_name not in self.plugins:
            logger.warning(f"⚠️ Plugin {plugin_name} not loaded")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            
            # Cleanup plugin
            if hasattr(plugin, 'cleanup'):
                plugin.cleanup()
            
            # Remove from registry
            del self.plugins[plugin_name]
            if plugin_name in self.plugin_metadata:
                del self.plugin_metadata[plugin_name]
            
            # Emit plugin unloaded event
            self.event_bus.emit('plugin_unloaded', {
                'plugin_name': plugin_name
            })
            
            logger.info(f"✅ Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin"""
        logger.info(f"🔄 Reloading plugin: {plugin_name}")
        
        # Unload first
        if plugin_name in self.plugins:
            if not self.unload_plugin(plugin_name):
                return False
        
        # Clear module from cache to force reload
        module_path = f"src.plugins.{plugin_name}"
        modules_to_remove = [
            key for key in sys.modules.keys() 
            if key.startswith(module_path)
        ]
        
        for module_key in modules_to_remove:
            del sys.modules[module_key]
        
        # Load again
        return self.load_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get a loaded plugin instance"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugins"""
        return self.plugins.copy()
    
    def get_plugin_names(self) -> List[str]:
        """Get names of all loaded plugins"""
        return list(self.plugins.keys())
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded"""
        return plugin_name in self.plugins
    
    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict]:
        """Get metadata for a plugin"""
        return self.plugin_metadata.get(plugin_name)
    
    def load_all(self, plugin_dir: str = "src/plugins/") -> Dict[str, bool]:
        """Load all discovered plugins"""
        logger.info(f"🚀 Loading all plugins from: {plugin_dir}")
        
        results = {}
        
        for plugin_name in self.discover_plugins(plugin_dir):
            results[plugin_name] = self.load_plugin(plugin_name, plugin_dir)
        
        loaded_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"🎯 Loaded {loaded_count}/{total_count} plugins")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics"""
        return {
            "total_plugins": len(self.plugins),
            "loaded_plugins": list(self.plugins.keys()),
            "plugin_metadata": self.plugin_metadata
        }