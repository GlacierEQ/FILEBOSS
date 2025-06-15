"""
Component Registry - Central registry for managing pluggable components
"""
import logging
import importlib
import inspect
from typing import Dict, Any, List, Type, Callable, Optional, Set, Union

logger = logging.getLogger("DeepSoul-ComponentRegistry")

class ComponentRegistry:
    """
    Central registry for DeepSeek-Coder components
    
    This registry allows components to be registered, discovered, and instantiated
    dynamically, making the system more modular and extensible.
    """
    
    def __init__(self):
        """Initialize the component registry"""
        # Component type registries
        self.scrapers = {}
        self.models = {}
        self.analyzers = {}
        self.enhancers = {}
        self.plugins = {}
        self.file_handlers = {}
        self.memory_optimizers = {}
        
        # Registry of all component types
        self.registry = {
            "scraper": self.scrapers,
            "model": self.models,
            "analyzer": self.analyzers,
            "enhancer": self.enhancers,
            "plugin": self.plugins,
            "file_handler": self.file_handlers,
            "memory_optimizer": self.memory_optimizers
        }
        
        # Registry of factory functions
        self.factories = {}
        
        # Registry of singleton instances
        self.singletons = {}
    
    def register(self, component_type: str, name: str, component_class: Type) -> None:
        """
        Register a component class
        
        Args:
            component_type: Type of component (e.g., "scraper", "model")
            name: Name to register the component under
            component_class: The component class
        """
        if component_type not in self.registry:
            logger.warning(f"Unknown component type: {component_type}")
            self.registry[component_type] = {}
        
        self.registry[component_type][name] = component_class
        logger.debug(f"Registered {component_type} component: {name}")
    
    def register_factory(self, component_type: str, name: str, factory_func: Callable) -> None:
        """
        Register a factory function for creating components
        
        Args:
            component_type: Type of component
            name: Name to register the factory under
            factory_func: Factory function
        """
        key = f"{component_type}.{name}"
        self.factories[key] = factory_func
        logger.debug(f"Registered factory for {component_type}: {name}")
    
    def get_component_class(self, component_type: str, name: str) -> Optional[Type]:
        """
        Get a registered component class
        
        Args:
            component_type: Type of component
            name: Name of the component
            
        Returns:
            Component class or None if not found
        """
        if component_type not in self.registry:
            return None
        
        return self.registry[component_type].get(name)
    
    def create_component(self, component_type: str, name: str, *args, **kwargs) -> Any:
        """
        Create a component instance
        
        Args:
            component_type: Type of component
            name: Name of the component
            *args, **kwargs: Arguments to pass to component constructor
            
        Returns:
            Component instance or None if not found
        """
        # Check for factory first
        factory_key = f"{component_type}.{name}"
        if factory_key in self.factories:
            return self.factories[factory_key](*args, **kwargs)
        
        # Otherwise use the class directly
        component_class = self.get_component_class(component_type, name)
        if component_class is None:
            logger.error(f"Component not found: {component_type}.{name}")
            return None
            
        try:
            return component_class(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error creating component {component_type}.{name}: {str(e)}")
            return None
    
    def get_singleton(self, component_type: str, name: str, *args, **kwargs) -> Any:
        """
        Get or create a singleton component instance
        
        Args:
            component_type: Type of component
            name: Name of the component
            *args, **kwargs: Arguments to pass to component constructor if needed
            
        Returns:
            Singleton component instance
        """
        singleton_key = f"{component_type}.{name}"
        
        if singleton_key in self.singletons:
            return self.singletons[singleton_key]
        
        # Create new instance
        instance = self.create_component(component_type, name, *args, **kwargs)
        
        if instance is not None:
            self.singletons[singleton_key] = instance
            
        return instance
    
    def get_available_components(self, component_type: str = None) -> Dict[str, List[str]]:
        """
        Get all available components
        
        Args:
            component_type: Optional component type filter
            
        Returns:
            Dictionary of component types to list of component names
        """
        if component_type is not None:
            if component_type not in self.registry:
                return {component_type: []}
            return {component_type: list(self.registry[component_type].keys())}
        
        # Return all component types and names
        return {
            ctype: list(components.keys())
            for ctype, components in self.registry.items()
            if components  # Only include non-empty registries
        }
    
    def auto_discover(self, module_paths: List[str]) -> int:
        """
        Auto-discover components in specified modules
        
        Args:
            module_paths: List of module paths to scan
            
        Returns:
            Number of components discovered
        """
        discovered = 0
        
        for module_path in module_paths:
            try:
                module = importlib.import_module(module_path)
                
                # Look for classes with component registration attributes
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        # Check for component_type attribute
                        component_type = getattr(obj, "_component_type", None)
                        component_name = getattr(obj, "_component_name", name)
                        
                        if component_type and component_type in self.registry:
                            self.register(component_type, component_name, obj)
                            discovered += 1
            
            except ImportError as e:
                logger.warning(f"Could not import module for auto-discovery: {module_path} - {str(e)}")
            except Exception as e:
                logger.error(f"Error during auto-discovery in {module_path}: {str(e)}")
        
        logger.info(f"Auto-discovered {discovered} components")
        return discovered

# Create singleton instance
_registry = ComponentRegistry()

def get_registry() -> ComponentRegistry:
    """Get the global component registry"""
    global _registry
    return _registry

def register_component(component_type: str, name: str = None):
    """
    Decorator for registering a component class
    
    Example:
        @register_component("scraper", "playwright")
        class PlaywrightScraper:
            ...
    
    Args:
        component_type: Type of component
        name: Optional name override (defaults to class name)
    """
    def decorator(cls):
        # Store component type and name as class attributes
        cls._component_type = component_type
        cls._component_name = name or cls.__name__
        
        # Register the component
        registry = get_registry()
        registry.register(component_type, cls._component_name, cls)
        
        return cls
    
    return decorator

def register_factory(component_type: str, name: str):
    """
    Decorator for registering a factory function
    
    Example:
        @register_factory("model", "deepseek-coder-1.3b")
        def create_model():
            return load_model("deepseek-ai/deepseek-coder-1.3b-instruct")
    
    Args:
        component_type: Type of component
        name: Name for the factory
    """
    def decorator(func):
        registry = get_registry()
        registry.register_factory(component_type, name, func)
        return func
    
    return decorator
