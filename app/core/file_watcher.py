"""
File system watcher that monitors directories for changes and sends WebSocket notifications.

This module provides a file system watcher that can monitor directories for changes
and send real-time notifications to connected WebSocket clients.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Set, Optional, Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileSystemMovedEvent

from app.core.websocket import WebSocketEventType, ConnectionManager

logger = logging.getLogger(__name__)

class FileSystemEventHandlerWrapper(FileSystemEventHandler):
    """Wrapper for file system events that forwards to WebSocket manager."""
    
    def __init__(self, callback: Callable[[str, str, dict], None], ignored_patterns: Optional[Set[str]] = None):
        """Initialize the event handler.
        
        Args:
            callback: Function to call when a file system event occurs
            ignored_patterns: Set of file patterns to ignore
        """
        self.callback = callback
        self.ignored_patterns = ignored_patterns or set()
    
    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored based on patterns."""
        path_str = str(path).lower()
        return any(pattern.lower() in path_str for pattern in self.ignored_patterns)
    
    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and not self._should_ignore(event.src_path):
            self.callback("created", event.src_path, {"is_directory": False})
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and not self._should_ignore(event.src_path):
            self.callback("deleted", event.src_path, {"is_directory": False})
    
    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and not self._should_ignore(event.src_path):
            # Skip directory modification events to avoid duplicate events
            self.callback("modified", event.src_path, {"is_directory": False})
    
    def on_moved(self, event: FileSystemMovedEvent) -> None:
        if not event.is_directory and not (self._should_ignore(event.src_path) or self._should_ignore(event.dest_path)):
            self.callback("moved", event.dest_path, {
                "is_directory": False,
                "old_path": event.src_path
            })

class FileSystemWatcher:
    """Watches file system changes and sends WebSocket notifications."""
    
    def __init__(self, websocket_manager: ConnectionManager):
        """Initialize the file system watcher.
        
        Args:
            websocket_manager: WebSocket connection manager to send notifications
        """
        self.websocket_manager = websocket_manager
        self.observer = Observer()
        self.watched_paths: Set[str] = set()
        self.ignored_patterns: Set[str] = {
            '*.tmp', '*.swp', '~*', '*.pyc', '__pycache__',
            '.git', '.idea', '.vscode', 'node_modules', 'venv', 'env'
        }
        self.running = False
    
    async def start(self) -> None:
        """Start the file system watcher."""
        if not self.running:
            self.observer.start()
            self.running = True
            logger.info("File system watcher started")
    
    async def stop(self) -> None:
        """Stop the file system watcher."""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("File system watcher stopped")
    
    async def watch_path(self, path: str) -> None:
        """Start watching a directory for changes.
        
        Args:
            path: Directory path to watch
            
        Raises:
            ValueError: If the path is not a directory or does not exist
        """
        path_obj = Path(path).resolve()
        path_str = str(path_obj)
        
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path_str}")
        if not path_obj.is_dir():
            raise ValueError(f"Path is not a directory: {path_str}")
        
        # Skip if already watching this path
        if path_str in self.watched_paths:
            return
        
        # Create event handler for this path
        handler = FileSystemEventHandlerWrapper(self._handle_file_event, self.ignored_patterns)
        
        # Schedule watching with watchdog
        self.observer.schedule(handler, path_str, recursive=True)
        self.watched_paths.add(path_str)
        logger.info(f"Now watching directory: {path_str}")
    
    async def unwatch_path(self, path: str) -> bool:
        """Stop watching a directory.
        
        Args:
            path: Directory path to stop watching
            
        Returns:
            bool: True if the path was being watched and was removed, False otherwise
        """
        path_str = str(Path(path).resolve())
        if path_str in self.watched_paths:
            # Note: watchdog doesn't provide a direct way to unschedule a specific watch,
            # so we'll just track it and filter events in the handler
            self.watched_paths.remove(path_str)
            logger.info(f"Stopped watching directory: {path_str}")
            return True
        return False
    
    def _handle_file_event(self, event_type: str, path: str, metadata: dict) -> None:
        """Handle a file system event and forward to WebSocket manager.
        
        Args:
            event_type: Type of file system event (created, modified, deleted, moved)
            path: Path to the affected file or directory
            metadata: Additional event metadata
        """
        try:
            # Map event types to our WebSocket event types
            event_mapping = {
                "created": WebSocketEventType.FILE_CREATED,
                "modified": WebSocketEventType.FILE_MODIFIED,
                "deleted": WebSocketEventType.FILE_DELETED,
                "moved": WebSocketEventType.FILE_MOVED,
            }
            
            ws_event_type = event_mapping.get(event_type)
            if not ws_event_type:
                return
            
            # Create WebSocket message
            message = {
                "event_type": ws_event_type.value,
                "data": {
                    "path": path,
                    "timestamp": asyncio.get_event_loop().time(),
                    **metadata
                }
            }
            
            # Broadcast to all clients watching this path or its parents
            path_obj = Path(path).resolve()
            
            # Check all parent directories to find watchers
            for watched_path in self.watched_paths:
                try:
                    rel_path = path_obj.relative_to(watched_path)
                    # If we get here, the path is inside a watched directory
                    asyncio.create_task(
                        self.websocket_manager.broadcast(
                            message,
                            path=watched_path
                        )
                    )
                    break
                except ValueError:
                    # Path is not in this watched directory
                    continue
                    
        except Exception as e:
            logger.error(f"Error handling file system event: {e}", exc_info=True)
