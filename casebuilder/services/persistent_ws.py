"""Persistent WebSocket client with auto-reconnect.

This module provides an asynchronous WebSocket client that automatically
reconnects when the connection drops. It can be used to maintain
long-lived WebSocket connections for event streaming or other
real-time features.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import websockets

logger = logging.getLogger(__name__)


class PersistentWebSocketClient:
    """Asynchronous WebSocket client with automatic reconnection."""

    def __init__(self, uri: str, reconnect_delay: float = 5.0) -> None:
        self.uri = uri
        self.reconnect_delay = reconnect_delay
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._task: Optional[asyncio.Task] = None
        self._connected = asyncio.Event()
        self._running = False

    async def connect(self) -> None:
        """Start the background connection task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        """Manage the connection and automatically reconnect on failure."""
        while self._running:
            try:
                logger.info("Connecting to %s", self.uri)
                async with websockets.connect(self.uri) as ws:
                    self._ws = ws
                    self._connected.set()
                    logger.info("WebSocket connected")
                    await ws.wait_closed()
            except Exception as exc:  # pragma: no cover - log and retry
                logger.warning("WebSocket error: %s", exc)
            finally:
                self._ws = None
                self._connected.clear()
                if self._running:
                    await asyncio.sleep(self.reconnect_delay)

    async def send(self, message: str) -> None:
        """Send a message once the connection is available."""
        await self._connected.wait()
        if self._ws is None:  # pragma: no cover - defensive
            raise RuntimeError("WebSocket not connected")
        await self._ws.send(message)

    async def recv(self) -> str:
        """Receive a message, waiting for connection if necessary."""
        await self._connected.wait()
        if self._ws is None:  # pragma: no cover - defensive
            raise RuntimeError("WebSocket not connected")
        return await self._ws.recv()

    async def close(self) -> None:
        """Stop the connection task and close the socket."""
        self._running = False
        self._connected.clear()
        if self._ws is not None:
            await self._ws.close()
        self._ws = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:  # pragma: no cover - expected
                pass

    async def __aenter__(self) -> "PersistentWebSocketClient":
        """Async context manager entry point."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Async context manager exit point."""
        await self.close()

