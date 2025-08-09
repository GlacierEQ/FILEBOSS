"""
Base integration class for APEX MANUS.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseIntegration')

class IntegrationConfig(BaseModel):
    """Base configuration model for integrations."""
    enabled: bool = True
    sync_interval: int = 300  # seconds
    last_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseIntegration(ABC):
    """
    Abstract base class for all APEX MANUS integrations.
    
    Attributes:
        name: Unique name of the integration
        description: Brief description of the integration
        version: Integration version
        config: Configuration for the integration
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialize the integration with optional configuration."""
        self.name = self.__class__.__name__
        self.description = self.__doc__ or ""
        self.version = "1.0.0"
        self.config = config or IntegrationConfig()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the integration."""
        if not self._initialized:
            logger.info(f"Initializing {self.name} integration")
            await self._setup()
            self._initialized = True
    
    @abstractmethod
    async def _setup(self) -> None:
        """Set up the integration. Should be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def sync(self) -> bool:
        """
        Synchronize data with the external service.
        
        Returns:
            bool: True if sync was successful, False otherwise
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the integration.
        
        Returns:
            Dict containing health status information
        """
        return {
            "name": self.name,
            "status": "healthy" if self._initialized else "uninitialized",
            "last_sync": self.config.last_sync.isoformat() if self.config.last_sync else None,
            "metadata": self.config.metadata
        }
    
    def __str__(self) -> str:
        return f"{self.name} (v{self.version}): {self.description}"
