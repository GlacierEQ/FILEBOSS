""
Integration manager for APEX MANUS.
"""
import asyncio
from typing import Dict, List, Optional, Type, TypeVar, Any
from datetime import datetime
import logging

from .base_integration import BaseIntegration, IntegrationConfig

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseIntegration)

class IntegrationManager:
    """
    Manages multiple integrations and handles synchronization between them.
    """
    
    def __init__(self):
        """Initialize the integration manager."""
        self._integrations: Dict[str, BaseIntegration] = {}
        self._sync_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
    
    async def add_integration(self, integration: BaseIntegration) -> None:
        """
        Add and initialize an integration.
        
        Args:
            integration: The integration instance to add
        """
        if integration.name in self._integrations:
            logger.warning(f"Integration {integration.name} already exists")
            return
            
        logger.info(f"Adding integration: {integration.name}")
        await integration.initialize()
        self._integrations[integration.name] = integration
    
    async def remove_integration(self, name: str) -> bool:
        """
        Remove an integration.
        
        Args:
            name: Name of the integration to remove
            
        Returns:
            bool: True if integration was removed, False otherwise
        """
        if name not in self._integrations:
            return False
            
        logger.info(f"Removing integration: {name}")
        if name in self._sync_tasks:
            self._sync_tasks[name].cancel()
            del self._sync_tasks[name]
            
        del self._integrations[name]
        return True
    
    async def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """
        Get an integration by name.
        
        Args:
            name: Name of the integration to get
            
        Returns:
            Optional[BaseIntegration]: The integration if found, None otherwise
        """
        return self._integrations.get(name)
    
    async def list_integrations(self) -> List[Dict[str, Any]]:
        """
        List all registered integrations with their status.
        
        Returns:
            List of integration status dictionaries
        """
        return [
            {
                "name": name,
                "description": integration.description,
                "version": integration.version,
                "enabled": integration.config.enabled,
                "last_sync": integration.config.last_sync.isoformat() 
                            if integration.config.last_sync else None
            }
            for name, integration in self._integrations.items()
        ]
    
    async def start(self) -> None:
        """Start all integrations and their sync tasks."""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting integration manager")
        
        for name, integration in self._integrations.items():
            if integration.config.enabled:
                self._start_integration_sync(name, integration)
    
    async def stop(self) -> None:
        """Stop all integrations and their sync tasks."""
        if not self._running:
            return
            
        self._running = False
        logger.info("Stopping integration manager")
        
        # Cancel all sync tasks
        for task in self._sync_tasks.values():
            task.cancel()
        
        # Wait for all tasks to complete
        if self._sync_tasks:
            await asyncio.gather(
                *self._sync_tasks.values(),
                return_exceptions=True
            )
    
    def _start_integration_sync(self, name: str, integration: BaseIntegration) -> None:
        """
        Start the sync task for an integration.
        
        Args:
            name: Name of the integration
            integration: The integration instance
        """
        async def _sync_loop() -> None:
            while self._running and integration.config.enabled:
                try:
                    logger.debug(f"Syncing {name}...")
                    success = await integration.sync()
                    if success:
                        integration.config.last_sync = datetime.utcnow()
                    logger.debug(f"Sync {'succeeded' if success else 'failed'} for {name}")
                except asyncio.CancelledError:
                    logger.info(f"Sync task for {name} cancelled")
                    raise
                except Exception as e:
                    logger.error(f"Error syncing {name}: {e}", exc_info=True)
                
                # Wait for the next sync interval
                try:
                    await asyncio.sleep(integration.config.sync_interval)
                except asyncio.CancelledError:
                    logger.info(f"Sync task for {name} cancelled during sleep")
                    raise
        
        # Cancel existing task if it exists
        if name in self._sync_tasks:
            self._sync_tasks[name].cancel()
        
        # Start new sync task
        self._sync_tasks[name] = asyncio.create_task(_sync_loop())
        logger.info(f"Started sync task for {name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Get the health status of all integrations.
        
        Returns:
            Dict containing health status of all integrations
        """
        health_checks = {}
        
        for name, integration in self._integrations.items():
            try:
                health_checks[name] = await integration.health_check()
            except Exception as e:
                health_checks[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "status": "running" if self._running else "stopped",
            "integrations": health_checks
        }
