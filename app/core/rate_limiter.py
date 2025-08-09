"""Rate limiting functionality for API endpoints."""
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.dependencies.utils import get_route_handler
from fastapi.routing import APIRoute
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError

class RateLimitConfig:
    """Configuration for rate limiting."""
    
    def __init__(
        self,
        requests: int = 100,
        window: int = 60,  # seconds
        scope: str = "global",  # 'global', 'user', 'ip', or 'endpoint'
        key_prefix: str = "rate_limit"
    ):
        self.requests = requests
        self.window = window
        self.scope = scope
        self.key_prefix = key_prefix
        
        # Validate scope
        if scope not in {"global", "user", "ip", "endpoint"}:
            raise ValueError("Invalid rate limit scope. Must be one of: global, user, ip, endpoint")

# In-memory rate limit store (replace with Redis in production)
_rate_limit_store: Dict[str, List[float]] = {}

def get_rate_limit_key(request: Request, config: RateLimitConfig) -> str:
    """Generate a unique key for rate limiting based on the scope."""
    key_parts = [config.key_prefix]
    
    if config.scope == "user":
        # Use user ID if authenticated, otherwise fall back to IP
        user = request.state.user if hasattr(request.state, "user") else None
        if user and hasattr(user, "id"):
            key_parts.append(f"user:{user.id}")
        else:
            key_parts.append(f"ip:{request.client.host}")
    elif config.scope == "ip":
        key_parts.append(f"ip:{request.client.host}")
    elif config.scope == "endpoint":
        key_parts.append(f"endpoint:{request.url.path}")
    
    return ":".join(key_parts)

async def check_rate_limit(request: Request, config: RateLimitConfig) -> None:
    """Check if the request exceeds the rate limit."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    key = get_rate_limit_key(request, config)
    current_time = time.time()
    
    # Initialize rate limit data if it doesn't exist
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []
    
    # Remove timestamps outside the current window
    window_start = current_time - config.window
    timestamps = [ts for ts in _rate_limit_store[key] if ts > window_start]
    
    # Check if rate limit is exceeded
    if len(timestamps) >= config.requests:
        retry_after = int(timestamps[0] + config.window - current_time)
        raise RateLimitExceededError(
            message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            retry_after=retry_after
        )
    
    # Add current timestamp and update the store
    timestamps.append(current_time)
    _rate_limit_store[key] = timestamps

class RateLimitMiddleware:
    """Middleware to enforce rate limits on API endpoints."""
    
    def __init__(
        self,
        app: ASGIApp,
        default_config: Optional[RateLimitConfig] = None,
        route_configs: Optional[Dict[str, RateLimitConfig]] = None
    ) -> None:
        self.app = app
        self.default_config = default_config or RateLimitConfig()
        self.route_configs = route_configs or {}
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive=receive)
        
        # Skip rate limiting for certain paths
        if request.url.path in {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}:
            await self.app(scope, receive, send)
            return
        
        # Get rate limit config for the current route
        route_config = self._get_route_config(request)
        
        if route_config:
            try:
                await check_rate_limit(request, route_config)
            except RateLimitExceededError as exc:
                response = JSONResponse(
                    status_code=exc.status_code,
                    content={
                        "success": False,
                        "error": exc.message,
                        "details": exc.details
                    },
                    headers=exc.headers
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def _get_route_config(self, request: Request) -> Optional[RateLimitConfig]:
        """Get rate limit configuration for the current route."""
        # Check for route-specific configuration
        for path_pattern, config in self.route_configs.items():
            if request.url.path.startswith(path_pattern):
                return config
        
        # Use default configuration
        return self.default_config

class RateLimitRoute(APIRoute):
    """Custom route class that applies rate limiting."""
    
    def __init__(
        self,
        *args,
        rate_limit_config: Optional[RateLimitConfig] = None,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.rate_limit_config = rate_limit_config
    
    def get_route_handler(self) -> Callable:
        """Get the route handler with rate limiting applied."""
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Any:
            if self.rate_limit_config:
                await check_rate_limit(request, self.rate_limit_config)
            return await original_route_handler(request)
        
        return custom_route_handler

def rate_limit(
    requests: int = 100,
    window: int = 60,
    scope: str = "ip",
    key_prefix: str = "rate_limit"
):
    """Decorator to apply rate limiting to a route.
    
    Args:
        requests: Number of requests allowed per window.
        window: Time window in seconds.
        scope: Scope of the rate limit ('global', 'user', 'ip', or 'endpoint').
        key_prefix: Prefix for the rate limit key.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request or not isinstance(request, Request):
                # Try to find the request in the arguments
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise ValueError("Request object not found in arguments")
            
            config = RateLimitConfig(
                requests=requests,
                window=window,
                scope=scope,
                key_prefix=key_prefix
            )
            
            await check_rate_limit(request, config)
            return await func(*args, **kwargs)
        
        # Preserve the original function's metadata
        wrapper.__name__ = func.__name__
        wrapper.__module__ = func.__module__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    
    return decorator
