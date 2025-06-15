"""
Service Manager - Manages system services and their lifecycle
"""
import logging
import threading
import time
from typing import Dict, List, Any, Callable, Optional, Set, Tuple

from .config_manager import ConfigManager

logger = logging.getLogger("DeepSoul-ServiceManager")

class Service:
    """Base class for all DeepSoul services"""
    
    # Class properties
    NAME = "base_service"
    DEPENDENCIES = []  # List of services this service depends on
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service
        
        Args:
            config: Service configuration
        """
        self.config = config or {}
        self.running = False
    
    def start(self) -> bool:
        """
        Start the service
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning(f"Service {self.NAME} is already running")
            return True
            
        logger.info(f"Starting service: {self.NAME}")
        self.running = True
        return True
    
    def stop(self) -> bool:
        """
        Stop the service
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.running:
            logger.debug(f"Service {self.NAME} is not running")
            return True
            
        logger.info(f"Stopping service: {self.NAME}")
        self.running = False
        return True
    
    def is_running(self) -> bool:
        """Check if the service is running"""
        return self.running

class ServiceManager:
    """Manages system services and their lifecycle"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the service manager
        
        Args:
            config_manager: Optional configuration manager
        """
        self.config_manager = config_manager or ConfigManager()
        self.services: Dict[str, Service] = {}
        self.service_threads: Dict[str, threading.Thread] = {}
        self.status_lock = threading.RLock()
    
    def register_service(self, service: Service) -> bool:
        """
        Register a service
        
        Args:
            service: Service instance
            
        Returns:
            True if registered successfully, False otherwise
        """
        with self.status_lock:
            if service.NAME in self.services:
                logger.warning(f"Service {service.NAME} is already registered")
                return False
                
            self.services[service.NAME] = service
            logger.info(f"Registered service: {service.NAME}")
            return True
    
    def start_service(self, name: str) -> bool:
        """
        Start a service by name
        
        Args:
            name: Service name
            
        Returns:
            True if started successfully, False otherwise
        """
        with self.status_lock:
            if name not in self.services:
                logger.error(f"Service not found: {name}")
                return False
                
            service = self.services[name]
            
            # Check dependencies
            for dependency in service.DEPENDENCIES:
                if dependency not in self.services:
                    logger.error(f"Missing dependency {dependency} for service {name}")
                    return False
                    
                if not self.services[dependency].is_running():
                    # Start dependency
                    logger.info(f"Starting dependency {dependency} for service {name}")
                    if not self.start_service(dependency):
                        logger.error(f"Failed to start dependency {dependency} for service {name}")
                        return False
            
            # Start the service
            if service.is_running():
                logger.info(f"Service {name} is already running")
                return True
                
            if service.start():
                logger.info(f"Started service: {name}")
                return True
            else:
                logger.error(f"Failed to start service: {name}")
                return False
    
    def stop_service(self, name: str) -> bool:
        """
        Stop a service by name
        
        Args:
            name: Service name
            
        Returns:
            True if stopped successfully, False otherwise
        """
        with self.status_lock:
            if name not in self.services:
                logger.error(f"Service not found: {name}")
                return False
                
            service = self.services[name]
            
            # Check for other services that depend on this one
            dependent_services = []
            for service_name, service_obj in self.services.items():
                if name in service_obj.DEPENDENCIES and service_obj.is_running():
                    dependent_services.append(service_name)
            
            # Stop dependent services first
            for dependent in dependent_services:
                logger.info(f"Stopping dependent service {dependent} before {name}")
                if not self.stop_service(dependent):
                    logger.error(f"Failed to stop dependent service {dependent}")
                    return False
            
            # Stop the service
            if not service.is_running():
                logger.info(f"Service {name} is not running")
                return True
                
            if service.stop():
                logger.info(f"Stopped service: {name}")
                return True
            else:
                logger.error(f"Failed to stop service: {name}")
                return False
    
    def start_all_services(self) -> Dict[str, bool]:
        """
        Start all registered services
        
        Returns:
            Dictionary mapping service names to success status
        """
        results = {}
        
        # Build dependency graph
        graph = {}
        for name, service in self.services.items():
            graph[name] = service.DEPENDENCIES
        
        # Find order using topological sort
        visited = set()
        temp = set()
        order = []
        
        def visit(name):
            if name in temp:
                logger.error(f"Circular dependency detected for service: {name}")
                return False
                
            if name in visited:
                return True
                
            temp.add(name)
            
            for dependency in graph.get(name, []):
                if dependency not in self.services:
                    logger.error(f"Missing dependency {dependency} for service {name}")
                    return False
                    
                if not visit(dependency):
                    return False
                    
            temp.remove(name)
            visited.add(name)
            order.append(name)
            return True
        
        # Visit all nodes
        for name in list(self.services.keys()):
            if not visit(name):
                return {name: False for name in self.services}
        
        # Start services in order
        for name in order:
            results[name] = self.start_service(name)
            
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """
        Stop all registered services
        
        Returns:
            Dictionary mapping service names to success status
        """
        results = {}
        
        # Build dependency graph (reversed)
        graph = {}
        for name, service in self.services.items():
            for dependency in service.DEPENDENCIES:
                if dependency not in graph:
                    graph[dependency] = []
                graph[dependency].append(name)
        
        # Add services with no dependents
        for name in self.services:
            if name not in graph:
                graph[name] = []
        
        # Find order using topological sort (reversed)
        visited = set()
        temp = set()
        order = []
        
        def visit(name):
            if name in temp:
                logger.error(f"Circular dependency detected for service: {name}")
                return False
                
            if name in visited:
                return True
                
            temp.add(name)
            
            for dependent in graph.get(name, []):
                if not visit(dependent):
                    return False
                    
            temp.remove(name)
            visited.add(name)
            order.append(name)
            return True
        
        # Visit all nodes
        for name in list(graph.keys()):
            if not visit(name):
                # Fallback to stopping in reverse order of dependencies
                order = list(self.services.keys())
                
        # Stop services in order
        for name in order:
            if name in self.services:
                results[name] = self.stop_service(name)
                
        return results
    
    def get_service(self, name: str) -> Optional[Service]:
        """
        Get a service by name
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not found
        """
        return self.services.get(name)
    
    def get_service_status(self) -> Dict[str, bool]:
        """
        Get status of all services
        
        Returns:
            Dictionary mapping service names to running status
        """
        with self.status_lock:
            return {
                name: service.is_running()
                for name, service in self.services.items()
            }

# Global instance
_service_manager = None

def get_service_manager() -> ServiceManager:
    """Get the global service manager instance"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager
