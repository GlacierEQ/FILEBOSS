"""WebSocket manager for real-time features."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, validator

from app.core.config import settings
from app.core.logging import logger


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_user_map: Dict[str, UUID] = {}
        self.user_connections_map: Dict[UUID, Set[str]] = {}
        self.channels: Dict[str, Set[str]] = {"global": set()}
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[UUID] = None) -> None:
        """Register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection.
            client_id: Unique identifier for the client.
            user_id: Optional user ID if the connection is authenticated.
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        if user_id:
            self.connection_user_map[client_id] = user_id
            if user_id not in self.user_connections_map:
                self.user_connections_map[user_id] = set()
            self.user_connections_map[user_id].add(client_id)
        
        # Add to global channel by default
        self.channels["global"].add(client_id)
        
        logger.info(f"Client connected: {client_id}" + (f" (User: {user_id})" if user_id else ""))
    
    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection.
        
        Args:
            client_id: The ID of the client to disconnect.
        """
        if client_id in self.active_connections:
            user_id = self.connection_user_map.get(client_id)
            
            # Remove from user connections
            if user_id and user_id in self.user_connections_map:
                self.user_connections_map[user_id].discard(client_id)
                if not self.user_connections_map[user_id]:
                    del self.user_connections_map[user_id]
            
            # Remove from channels
            for channel in self.channels.values():
                channel.discard(client_id)
            
            # Remove from active connections
            if client_id in self.connection_user_map:
                del self.connection_user_map[client_id]
            
            del self.active_connections[client_id]
            logger.info(f"Client disconnected: {client_id}" + (f" (User: {user_id})" if user_id else ""))
    
    async def send_personal_message(self, message: Union[dict, str], client_id: str) -> None:
        """Send a message to a specific client.
        
        Args:
            message: The message to send (dict or JSON string).
            client_id: The ID of the client to send the message to.
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                if isinstance(message, dict):
                    message = json.dumps(message)
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Union[dict, str], channel: str = "global") -> None:
        """Send a message to all active connections in a channel.
        
        Args:
            message: The message to broadcast (dict or JSON string).
            channel: The channel to broadcast to (default: "global").
        """
        if channel not in self.channels:
            logger.warning(f"Attempted to broadcast to non-existent channel: {channel}")
            return
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        disconnected_clients = []
        
        for client_id in list(self.channels[channel]):
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def send_to_user(self, user_id: UUID, message: Union[dict, str]) -> None:
        """Send a message to all connections for a specific user.
        
        Args:
            user_id: The ID of the user to send the message to.
            message: The message to send (dict or JSON string).
        """
        if user_id not in self.user_connections_map:
            return
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        disconnected_clients = []
        
        for client_id in list(self.user_connections_map[user_id]):
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def subscribe(self, client_id: str, channel: str) -> None:
        """Subscribe a client to a channel.
        
        Args:
            client_id: The ID of the client to subscribe.
            channel: The channel to subscribe to.
        """
        if client_id not in self.active_connections:
            return
        
        if channel not in self.channels:
            self.channels[channel] = set()
        
        self.channels[channel].add(client_id)
        logger.debug(f"Client {client_id} subscribed to {channel}")
    
    def unsubscribe(self, client_id: str, channel: str) -> None:
        """Unsubscribe a client from a channel.
        
        Args:
            client_id: The ID of the client to unsubscribe.
            channel: The channel to unsubscribe from.
        """
        if channel in self.channels and client_id in self.channels[channel]:
            self.channels[channel].remove(client_id)
            logger.debug(f"Client {client_id} unsubscribed from {channel}")


class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            # Add custom JSON encoders if needed
        }


class WebSocketClient:
    """WebSocket client wrapper for handling connections."""
    
    def __init__(self, websocket: WebSocket, client_id: str, manager: ConnectionManager):
        """Initialize the WebSocket client.
        
        Args:
            websocket: The WebSocket connection.
            client_id: Unique identifier for the client.
            manager: The connection manager.
        """
        self.websocket = websocket
        self.client_id = client_id
        self.manager = manager
        self.user_id: Optional[UUID] = None
        self.authenticated = False
    
    async def authenticate(self, user_id: UUID) -> None:
        """Authenticate the WebSocket connection with a user ID.
        
        Args:
            user_id: The ID of the authenticated user.
        """
        self.user_id = user_id
        self.authenticated = True
        
        # Update the connection manager
        self.manager.connection_user_map[self.client_id] = user_id
        if user_id not in self.manager.user_connections_map:
            self.manager.user_connections_map[user_id] = set()
        self.manager.user_connections_map[user_id].add(self.client_id)
        
        logger.info(f"WebSocket client {self.client_id} authenticated as user {user_id}")
    
    async def send(self, message: Union[dict, str, WebSocketMessage]) -> None:
        """Send a message to the client.
        
        Args:
            message: The message to send.
        """
        if isinstance(message, WebSocketMessage):
            message = message.dict(exclude_none=True)
        await self.manager.send_personal_message(message, self.client_id)
    
    async def receive_json(self) -> dict:
        """Receive a JSON message from the client.
        
        Returns:
            The parsed JSON message as a dictionary.
        """
        try:
            message = await self.websocket.receive_text()
            return json.loads(message)
        except json.JSONDecodeError as e:
            await self.send({"type": "error", "message": "Invalid JSON format"})
            raise
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            await self.send({"type": "error", "message": "Internal server error"})
            raise
    
    async def handle_message(self, message: dict) -> None:
        """Handle an incoming WebSocket message.
        
        Args:
            message: The received message.
        """
        try:
            # Handle different message types
            msg_type = message.get("type")
            request_id = message.get("request_id")
            
            if msg_type == "ping":
                await self.send({"type": "pong", "request_id": request_id})
            
            elif msg_type == "auth":
                # Handle authentication
                token = message.get("data", {}).get("token")
                if not token:
                    await self.send({"type": "auth_error", "message": "No token provided", "request_id": request_id})
                    return
                
                # TODO: Validate token and get user ID
                # user_id = await validate_websocket_token(token)
                # if user_id:
                #     await self.authenticate(user_id)
                #     await self.send({"type": "auth_success", "user_id": str(user_id), "request_id": request_id})
                # else:
                #     await self.send({"type": "auth_error", "message": "Invalid token", "request_id": request_id})
                await self.send({"type": "auth_error", "message": "Authentication not implemented", "request_id": request_id})
            
            elif msg_type == "subscribe":
                # Handle channel subscription
                channel = message.get("data", {}).get("channel")
                if not channel:
                    await self.send({"type": "error", "message": "No channel specified", "request_id": request_id})
                    return
                
                self.manager.subscribe(self.client_id, channel)
                await self.send({"type": "subscribed", "channel": channel, "request_id": request_id})
            
            elif msg_type == "unsubscribe":
                # Handle channel unsubscription
                channel = message.get("data", {}).get("channel")
                if not channel:
                    await self.send({"type": "error", "message": "No channel specified", "request_id": request_id})
                    return
                
                self.manager.unsubscribe(self.client_id, channel)
                await self.send({"type": "unsubscribed", "channel": channel, "request_id": request_id})
            
            else:
                # Unknown message type
                await self.send({"type": "error", "message": f"Unknown message type: {msg_type}", "request_id": request_id})
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send({"type": "error", "message": "Error processing message", "request_id": message.get("request_id")})


# Global WebSocket manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections."""
    client_id = str(uuid4())
    client = WebSocketClient(websocket, client_id, manager)
    
    try:
        # Accept the WebSocket connection
        await manager.connect(websocket, client_id)
        
        # Send welcome message
        await client.send({
            "type": "welcome",
            "client_id": client_id,
            "server_info": {
                "name": settings.PROJECT_NAME,
                "version": "1.0.0"
            }
        })
        
        # Handle incoming messages
        while True:
            try:
                message = await client.receive_json()
                await client.handle_message(message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on errors
    
    except WebSocketDisconnect:
        pass  # Client disconnected normally
    
    finally:
        # Clean up
        manager.disconnect(client_id)
