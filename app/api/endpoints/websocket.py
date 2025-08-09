"""WebSocket endpoints for real-time communication."""
import asyncio
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, Request, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.websocket import ConnectionManager, WebSocketMessage, WebSocketEventType
from app.core.file_watcher import FileSystemWatcher
from app.core.config import settings
from app.models.user import UserInDB
from app.core.logging import logger
from app.core.security import get_current_user_from_token

# Initialize router
router = APIRouter()

# Initialize WebSocket manager and file watcher
websocket_manager = ConnectionManager()
file_watcher = FileSystemWatcher(websocket_manager)

# Start the file watcher when the module loads
@router.on_event("startup")
async def startup_event():
    """Start the file system watcher when the application starts."""
    await file_watcher.start()

# Stop the file watcher when the application shuts down
@router.on_event("shutdown")
async def shutdown_event():
    """Stop the file system watcher when the application shuts down."""
    await file_watcher.stop()

# Initialize templates
try:
    templates = Jinja2Templates(directory="app/templates")
except Exception as e:
    logger.warning(f"Failed to load templates: {e}")
    templates = None

async def get_current_user_ws(token: str) -> Optional[UserInDB]:
    """Get the current user from a WebSocket token.
    
    Args:
        token: JWT token from WebSocket connection
        
    Returns:
        UserInDB if authentication is successful, None otherwise
    """
    try:
        user = await get_current_user_from_token(token)
        return user
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Authentication token"),
):
    """WebSocket endpoint for real-time communication.
    
    This endpoint establishes a WebSocket connection for real-time communication.
    It can handle both authenticated and unauthenticated connections with limited functionality.
    
    Args:
        websocket: The WebSocket connection
        token: Optional authentication token for authenticated connections
    """
    # Generate a unique ID for this connection
    client_id = str(uuid.uuid4())
    
    try:
        # Accept the WebSocket connection
        await websocket_manager.connect(websocket, client_id)
        logger.info(f"New WebSocket connection: {client_id}")
        
        # If token is provided, authenticate the user
        if token:
            user = await get_current_user_ws(token)
            if user:
                await websocket_manager.authenticate_client(client_id, token)
        
        # Main message loop
        while True:
            try:
                # Wait for any message from the client
                data = await websocket.receive_json()
                
                # Handle the message
                await websocket_manager.handle_message(client_id, data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {client_id}")
                break
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                await websocket_manager.send_personal_message(
                    WebSocketMessage(
                        event_type=WebSocketEventType.ERROR,
                        data={"message": f"Error processing message: {str(e)}"}
                    ),
                    client_id
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    
    finally:
        # Clean up on disconnect
        websocket_manager.disconnect(client_id)
        logger.info(f"WebSocket connection closed: {client_id}")

@router.get("/ws/connections")
async def get_active_connections():
    """Get information about active WebSocket connections."""
    return {
        "total_connections": len(websocket_manager.active_connections),
        "authenticated_connections": len(websocket_manager.authenticated_clients),
        "watched_paths": {
            client_id: list(paths) 
            for client_id, paths in websocket_manager.watched_paths.items()
        },
        "client_info": websocket_manager.client_info,
    }

@router.get("/ws/watcher/status")
async def get_watcher_status():
    """Get the status of the file system watcher."""
    return {
        "running": file_watcher.running,
        "watched_paths": list(file_watcher.watched_paths),
    }

@router.post("/ws/watch")
async def watch_path(path: str, recursive: bool = True):
    """Start watching a directory for changes."""
    try:
        await file_watcher.watch_path(path)
        return {"status": "success", "message": f"Now watching path: {path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/ws/watch")
async def unwatch_path(path: str):
    """Stop watching a directory."""
    try:
        success = await file_watcher.unwatch_path(path)
        if success:
            return {"status": "success", "message": f"Stopped watching path: {path}"}
        else:
            return {"status": "not_found", "message": f"Path not being watched: {path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ws-test", response_class=HTMLResponse)
async def websocket_test_page(request: Request):
    """Render a test page for WebSocket connections."""
    if not templates:
        return HTMLResponse("<h1>Templates not available</h1>")
    
    websocket_url = f"{settings.WEBSOCKET_URL or 'ws' + settings.SERVER_NAME + '/api/v1/ws'}"
    
    return templates.TemplateResponse(
        "websocket_test.html",
        {
            "request": request,
            "websocket_url": websocket_url,
            "project_name": settings.PROJECT_NAME,
        },
    )
