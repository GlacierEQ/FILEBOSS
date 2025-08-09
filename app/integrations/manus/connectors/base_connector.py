"""
Base connector class for external service integrations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging

from ..core.base_integration import BaseIntegration, IntegrationConfig

logger = logging.getLogger(__name__)

class BaseConnector(ABC):
    """
    Abstract base class for all external service connectors.
    
    Attributes:
        name: Name of the connector
        service_name: Name of the external service
        base_url: Base URL for the service API
        auth_type: Type of authentication required (e.g., 'oauth2', 'api_key')
        rate_limit: Maximum requests per minute
        last_request: Timestamp of the last API request
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialize the connector with optional configuration."""
        self.name = self.__class__.__name__
        self.service_name = ""
        self.base_url = ""
        self.auth_type = "none"
        self.rate_limit = 60  # requests per minute
        self.last_request: Optional[datetime] = None
        self.config = config or IntegrationConfig()
        self._session = None
    
    @abstractmethod
    async def connect(self, **kwargs) -> bool:
        """
        Establish connection to the external service.
        
        Args:
            **kwargs: Connection parameters (API keys, tokens, etc.)
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the external service."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test the connection to the external service.
        
        Returns:
            bool: True if the test was successful, False otherwise
        """
        pass
    
    async def _rate_limit_delay(self) -> None:
        """
        Handle rate limiting by delaying requests if necessary.
        """
        if self.last_request and self.rate_limit > 0:
            time_since_last = (datetime.utcnow() - self.last_request).total_seconds()
            min_interval = 60.0 / self.rate_limit
            
            if time_since_last < min_interval:
                delay = min_interval - time_since_last
                logger.debug(f"Rate limiting: waiting {delay:.2f}s before next request")
                await asyncio.sleep(delay)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the external service.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            Dict containing the response data
            
        Raises:
            Exception: If the request fails
        """
        await self._rate_limit_delay()
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.debug(f"Making {method.upper()} request to {url}")
        
        try:
            # TODO: Implement actual HTTP request logic using aiohttp or similar
            # This is a placeholder implementation
            self.last_request = datetime.utcnow()
            
            # Simulate request/response
            return {
                "status": "success",
                "data": {},
                "metadata": {
                    "url": url,
                    "method": method,
                    "timestamp": self.last_request.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            raise
    
    def __str__(self) -> str:
        return f"{self.name} ({self.service_name} connector)"
