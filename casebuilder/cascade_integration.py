"""
Cascade Integration Module

This module provides integration with the Cascade AI assistant, handling initialization,
configuration, and communication with the Cascade service.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseSettings, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CascadeConfig(BaseSettings):
    """Configuration for Cascade integration."""
    CASCADE_API_KEY: str = Field(..., env='CASCADE_API_KEY')
    CACHE_DIR: Path = Path.home() / '.cache' / 'casebuilder' / 'cascade'
    REQUEST_TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # seconds

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

class CascadeIntegration:
    """Handles integration with the Cascade AI assistant."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CascadeIntegration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = CascadeConfig()
        self._ensure_cache_dir()
        self._setup_http_client()
        self._initialized = True
        logger.info("Cascade integration initialized")
    
    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        try:
            self.config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise
    
    def _setup_http_client(self) -> None:
        """Set up the HTTP client with retry logic and timeouts."""
        import httpx
        
        self.client = httpx.AsyncClient(
            timeout=self.config.REQUEST_TIMEOUT,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
            follow_redirects=True,
        )
    
    async def query_cascade(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the Cascade AI assistant with the given prompt and optional context.
        
        Args:
            prompt: The user's query or prompt
            context: Additional context for the query
            
        Returns:
            Dict containing the response from Cascade
        """
        import httpx
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        @retry(
            stop=stop_after_attempt(self.config.MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True
        )
        async def _send_request() -> Dict[str, Any]:
            """Send request to Cascade API with retry logic."""
            try:
                headers = {
                    "Authorization": f"Bearer {self.config.CASCADE_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "prompt": prompt,
                    "context": context or {}
                }
                
                response = await self.client.post(
                    "https://api.cascade.ai/v1/query",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error querying Cascade: {str(e)}")
                raise
        
        return await _send_request()
    
    async def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'client'):
            await self.client.aclose()
            logger.info("Cascade HTTP client closed")

# Global instance for easy access
cascade = CascadeIntegration()

# Cleanup on application shutdown
import atexit
import asyncio

def cleanup():
    """Synchronously clean up resources."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cascade.close())
        else:
            loop.run_until_complete(cascade.close())
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

atexit.register(cleanup)
