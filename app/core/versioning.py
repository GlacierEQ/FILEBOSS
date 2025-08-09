"""API versioning utilities."""
from enum import Enum
from typing import Callable, Optional, TypeVar, cast

from fastapi import APIRouter, FastAPI, Request
from fastapi.routing import APIRoute
from starlette.routing import Route, WebSocketRoute

from app.core.config import settings

# Type variable for generic function type
F = TypeVar("F", bound=Callable)


class ApiVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    V2 = "v2"  # Future version


def version(api_version: ApiVersion) -> Callable[[F], F]:
    """Decorator to mark a route as belonging to a specific API version.
    
    Args:
        api_version: The API version this route belongs to.
    """
    def decorator(func: F) -> F:
        if not hasattr(func, "_api_versions"):
            func._api_versions = set()  # type: ignore
        func._api_versions.add(api_version)  # type: ignore
        return func
    return decorator


def get_api_version(request: Request) -> ApiVersion:
    """Get the API version from the request.
    
    This checks the URL path first, then falls back to the Accept header.
    """
    # Check URL path first (e.g., /api/v1/users)
    path_parts = request.url.path.split("/")
    if len(path_parts) > 2 and path_parts[1] == "api":
        version_part = path_parts[2].lower()
        try:
            return ApiVersion(version_part)
        except ValueError:
            pass
    
    # Fall back to Accept header (e.g., application/vnd.myapp.v1+json)
    accept = request.headers.get("accept", "")
    for version_ in ApiVersion:
        if f"vnd.{settings.PROJECT_NAME.lower()}.{version_.value}" in accept:
            return version_
    
    # Default to the latest stable version
    return ApiVersion.V1


class VersionedAPIRoute(APIRoute):
    """Custom route that supports API versioning."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.versions = set()
        
        # Extract versions from the route function
        if hasattr(self.endpoint, "_api_versions"):
            self.versions = getattr(self.endpoint, "_api_versions")
    
    def matches(self, scope: dict) -> tuple[bool, dict]:
        match, child_scope = super().matches(scope)
        if not match:
            return False, {}
            
        # Check if the requested version matches any of the route's versions
        request = Request(scope)
        requested_version = get_api_version(request)
        
        if self.versions and requested_version not in self.versions:
            return False, {}
            
        return True, child_scope


class VersionedAPIRouter(APIRouter):
    """Custom router that supports API versioning."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.route_class = VersionedAPIRoute
    
    def add_api_route(
        self,
        path: str,
        endpoint: Callable,
        *,
        versions: Optional[list[ApiVersion]] = None,
        **kwargs
    ) -> None:
        """Add a route with versioning support."""
        if versions:
            for version_ in versions:
                endpoint = version(version_)(endpoint)
        super().add_api_route(path, endpoint, **kwargs)


def setup_api_versioning(app: FastAPI) -> None:
    """Set up API versioning for the FastAPI application."""
    # Add versioning middleware
    @app.middleware("http")
    async def versioning_middleware(request: Request, call_next):
        # Get the requested version
        version = get_api_version(request)
        
        # Add version to request state
        request.state.api_version = version
        
        # Process the request
        response = await call_next(request)
        
        # Add version to response headers
        response.headers["X-API-Version"] = version.value
        return response
    
    # Add versioned routes
    app.include_router(
        api_v1_router,
        prefix="/api/v1",
        tags=["v1"],
        responses={404: {"description": "Not found"}},
    )
    
    # Add a catch-all route for the latest version
    @app.get("/api")
    async def redirect_to_latest():
        return {
            "message": f"Please use a specific API version. Latest is v1.",
            "latest_version": "v1",
            "docs": "/api/v1/docs"
        }


# Create versioned routers
api_v1_router = VersionedAPIRouter(
    prefix="",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

# Future version
api_v2_router = VersionedAPIRouter(
    prefix="",
    tags=["v2"],
    responses={404: {"description": "Not found"}},
)

# Export the main router for v1 to be used in the application
router = api_v1_router
