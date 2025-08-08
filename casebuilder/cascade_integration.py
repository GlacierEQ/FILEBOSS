"""
Cascade Integration Module

This module provides integration with the Cascade AI assistant, handling initialization,
configuration, and communication with the Cascade service.
"""
import os
import logging
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from pydantic import Field, HttpUrl, validator
from pydantic_settings import BaseSettings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from datetime import datetime, timedelta
import aiofiles
import hashlib
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CascadeConfig(BaseSettings):
    """Configuration for Cascade integration."""
    CASCADE_API_KEY: str = Field(..., env='CASCADE_API_KEY')
    CASCADE_API_URL: HttpUrl = Field("https://api.cascade.ai/v1", env='CASCADE_API_URL')
    CACHE_DIR: Path = Field(Path.home() / '.cache' / 'casebuilder' / 'cascade', env='CACHE_DIR')
    REQUEST_TIMEOUT: int = Field(30, env='CASCADE_REQUEST_TIMEOUT')
    MAX_RETRIES: int = Field(3, env='CASCADE_MAX_RETRIES')
    RETRY_DELAY: float = Field(1.0, env='CASCADE_RETRY_DELAY')
    CACHE_TTL: int = Field(3600, env='CACHE_TTL')  # 1 hour default TTL
    ENABLE_CACHE: bool = Field(True, env='CACHE_ENABLED')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False

    @validator('CACHE_DIR', pre=True, always=True)
    def ensure_cache_dir_exists(cls, v):
        """Ensure cache directory exists."""
        path = Path(v)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            logger.warning(f"Failed to create cache directory {path}: {e}")
            # Fallback to system temp dir
            import tempfile
            temp_cache = Path(tempfile.gettempdir()) / 'casebuilder-cache'
            temp_cache.mkdir(exist_ok=True)
            return temp_cache

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
        self._http_client = None
        self._cache = {}
        self._initialized = True
        self._session_id = self._generate_session_id()
        logger.info(f"Cascade integration initialized (Session: {self._session_id})")

    def _generate_session_id(self) -> str:
        """Generate a unique session ID for this instance."""
        return hashlib.md5(
            f"{platform.node()}-{os.getpid()}-{datetime.now().timestamp()}"
            .encode()
        ).hexdigest()

    def _get_cache_key(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Generate a cache key for the given prompt and context."""
        cache_str = f"{prompt}-{json.dumps(context or {}, sort_keys=True)}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    async def _load_from_cache(self, key: str) -> Optional[Dict]:
        """Load a response from cache if it exists and is not expired."""
        if not self.config.ENABLE_CACHE:
            return None

        cache_file = self.config.CACHE_DIR / f"{key}.json"

        try:
            if cache_file.exists():
                async with aiofiles.open(cache_file, 'r') as f:
                    data = json.loads(await f.read())
                    cache_time = datetime.fromisoformat(data['timestamp'])

                    if datetime.now() - cache_time < timedelta(seconds=self.config.CACHE_TTL):
                        logger.debug(f"Cache hit for key: {key}")
                        return data['response']
                    else:
                        logger.debug(f"Cache expired for key: {key}")
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")

        return None

    async def _save_to_cache(self, key: str, response: Dict) -> None:
        """Save a response to cache."""
        if not self.config.ENABLE_CACHE:
            return

        cache_file = self.config.CACHE_DIR / f"{key}.json"

        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'response': response
            }
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(data))
        except Exception as e:
            logger.warning(f"Error writing to cache: {e}")

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy-load HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.REQUEST_TIMEOUT,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                ),
                follow_redirects=True,
                headers={
                    'User-Agent': f'CaseBuilder/{self._session_id}'
                }
            )
        return self._http_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=(
            retry_if_exception_type(httpx.HTTPStatusError) |
            retry_if_exception_type(httpx.RequestError) |
            retry_if_exception_type(asyncio.TimeoutError)
        ),
        reraise=True
    )
    async def query_cascade(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Query the Cascade AI assistant.

        Args:
            prompt: The user's query or prompt
            context: Additional context for the query
            use_cache: Whether to use cached responses when available

        Returns:
            Dict containing the response from Cascade
        """
        cache_key = self._get_cache_key(prompt, context)

        # Try to get from cache first
        if use_cache:
            cached = await self._load_from_cache(cache_key)
            if cached is not None:
                return cached

        # Prepare the request
        headers = {
            "Authorization": f"Bearer {self.config.CASCADE_API_KEY}",
            "Content-Type": "application/json",
            "X-Session-ID": self._session_id
        }

        payload = {
            "prompt": prompt,
            "context": context or {},
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "casebuilder"
            }
        }

        try:
            # Make the API request
            response = await self.http_client.post(
                f"{self.config.CASCADE_API_URL}/query",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()

            # Cache the successful response
            if use_cache and result.get('status') == 'success':
                await self._save_to_cache(cache_key, result)

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            error_msg = f"Failed to decode JSON response: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except Exception as e:
            logger.error(f"Error querying Cascade: {str(e)}")
            raise

    async def close(self) -> None:
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            logger.info("HTTP client closed")

# Global instance for easy access
cascade = CascadeIntegration()

# Cleanup on application shutdown
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

import atexit
atexit.register(cleanup)
