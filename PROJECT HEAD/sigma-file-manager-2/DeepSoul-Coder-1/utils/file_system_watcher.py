"""
File System Watcher - Monitor file system changes and trigger appropriate actions
"""
import os
import sys
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Set, Callable, Optional, Any
from datetime import datetime
from queue import Queue

# For cross-platform file system monitoring
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent, 
    FileDeletedEvent, DirCreatedEvent, DirModifiedEvent, DirDeletedEvent
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_manager import get_memory_manager

logger = logging.getLogger("DeepSoul-FileSystemWatcher")

class DeepSoulEventHandler(FileSystemEventHandler):
    """Custom event handler for DeepSoul file system monitoring"""
    
    def __init__(self, callback_manager):
        """Initialize with a callback manager"""
        self.callback_manager = callback_manager
        self.memory_manager = get_memory_manager()
        
        # Debounce mechanism to prevent duplicate events
        self.last_events = {}
        self.debounce_seconds = 2.0
        
        # Specific ignored patterns
        self.ignored_dirs = {'.git', '.idea', '__pycache__', 'venv', 'node_modules'}
        self.ignored_extensions = {'.pyc', '.pyo', '.pyd', '.git', '.tmp'}
    
    def should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored"""
        path_obj = Path(path)
        
        # Check for ignored directories
        for part in path_obj.parts:
            if part in self.ignored_dirs:
                return True
        
        # Check for ignored extensions
        if path_obj.suffix.lower() in self.ignored_extensions:
            return True
            
        # Ignore temporary files
        if path_obj.name.startswith('.') or path_obj.name.startswith('~'):
            return True
            
        return False
    
    def is_debounced(self, event_path: str, event_type: str) -> bool:
        """Check if an event should be debounced"""
        event_key = f"{event_path}:{event_type}"
        current_time = time.time()
        
        # Check if we've seen this event recently
        if event_key in self.last_events:
            last_time = self.last_events[event_key]
            if current_time - last_time < self.debounce_seconds:
                return True
        
        # Update the last event time
        self.last_events[event_key] = current_time
        
        # Clean up old events
        self._cleanup_old_events(current_time)
        
        return False
    
    def _cleanup_old_events(self, current_time: float):
        """Clean up old events from the debounce cache"""
        keys_to_remove = []
        for key, timestamp in self.last_events.items():
            if current_time - timestamp > self.debounce_seconds * 10:  # Keep for 10x debounce time
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.last_events[key]
    
    def on_created(self, event):
        """Handle file/directory creation events"""
        if self.should_ignore(event.src_path) or self.is_debounced(event.src_path, 'created'):
            return
            
        if event.is_directory:
            self.callback_manager.trigger('dir_created', event.src_path)
        else:
            self.callback_manager.trigger('file_created', event.src_path)
    
    def on_modified(self, event):
        """Handle file/directory modification events"""
        if self.should_ignore(event.src_path) or self.is_debounced(event.src_path, 'modified'):
            return
            
        if event.is_directory:
            self.callback_manager.trigger('dir_modified', event.src_path)
        else:
            self.callback_manager.trigger('file_modified', event.src_path)
    
    def on_deleted(self, event):
        """Handle file/directory deletion events"""
        if self.should_ignore(event.src_path) or self.is_debounced(event.src_path, 'deleted'):
            return
            
        if event.is_directory:
            self.callback_manager.trigger('dir_deleted', event.src_path)
        else:
            self.callback_manager.trigger('file_deleted', event.src_path)
    
    def on_moved(self, event):
        """Handle file/directory move events"""
        if self.should_ignore(event.src_path) or self.should_ignore(event.dest_path) or \
           self.is_debounced(f"{event.src_path}->{event.dest_path}", 'moved'):
            return
            
        if event.is_directory:
            self.callback_manager.trigger('dir_moved', event.src_path, event.dest_path)
        else:
            self.callback_manager.trigger('file_moved', event.src_path, event.dest_path)


class FileSystemWatcher:
    """
    Manages file system watching and triggers appropriate callbacks for file events
    
    This class monitors specified directories for file changes and triggers custom actions 
    in response to file system events.
    """
    
    def __init__(self):
        """Initialize the file system watcher"""
        self.observers = {}
        self.watched_paths = set()
        self.callbacks = {
            'file_created': [],
            'file_modified': [],
            'file_deleted': [],
            'file_moved': [],
            'dir_created': [],
            'dir_modified': [],
            'dir_deleted': [],
            'dir_moved': []
        }
        
        # Common code file extensions
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.java', '.kt', '.rb', '.go',
            '.rs', '.php', '.swift', '.m', '.dart', '.sh', '.bash', '.ps1',
            '.sql', '.yaml', '.yml', '.json', '.xml', '.md', '.rst'
        }
        
        # Event processing queue and thread
        self.event_queue = Queue()
        self.processing_thread = None
        self.running = False
    
    def start(self):
        """Start the file system watcher and event processing"""
        if self.running:
            logger.warning("File system watcher is already running")
            return
            
        self.running = True
        
        # Start event processing thread
        self.processing_thread = threading.Thread(
            target=self._event_processing_loop,
            name="FileSystemEventProcessor",
            daemon=True
        )
        self.processing_thread.start()
        
        # Start all observers
        for path, observer in self.observers.items():
            if not observer.is_alive():
                observer.start()
                logger.info(f"Started watching: {path}")
        
        logger.info("File system watcher started")
    
    def stop(self):
        """Stop the file system watcher and event processing"""
        if not self.running:
            return
            
        self.running = False
        
        # Stop all observers
        for path, observer in self.observers.items():
            if observer.is_alive():
                observer.stop()
                logger.info(f"Stopped watching: {path}")
        
        # Wait for observers to stop
        for path, observer in self.observers.items():
            observer.join(timeout=2.0)
        
        # Clear the observers
        self.observers = {}
        self.watched_paths = set()
        
        # Stop processing thread
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
            
        logger.info("File system watcher stopped")
    
    def watch_directory(self, path: str, recursive: bool = True):
        """
        Watch a directory for changes
        
        Args:
            path: Directory path to watch
            recursive: Whether to watch subdirectories
        """
        # Normalize path
        path = os.path.abspath(path)
        
        # Check if path exists
        if not os.path.isdir(path):
            logger.error(f"Path does not exist or is not a directory: {path}")
            return False
            
        # Check if already watching
        if path in self.watched_paths:
            logger.warning(f"Already watching path: {path}")
            return True
            
        # Create event handler
        event_handler = DeepSoulEventHandler(self)
        
        # Create observer for this path
        observer = Observer()
        observer.schedule(event_handler, path, recursive=recursive)
        
        # Store observer
        self.observers[path] = observer
        self.watched_paths.add(path)
        
        # Start observer if watcher is running
        if self.running:
            observer.start()
            logger.info(f"Started watching path: {path}")
        
        logger.info(f"Added path to watch list: {path}")
        return True
    
    def unwatch_directory(self, path: str) -> bool:
        """
        Stop watching a directory
        
        Args:
            path: Directory path to stop watching
            
        Returns:
            True if successful, False otherwise
        """
        # Normalize path
        path = os.path.abspath(path)
        
        # Check if watching this path
        if path not in self.watched_paths:
            logger.warning(f"Not watching path: {path}")
            return False
            
        # Stop and remove observer
        observer = self.observers[path]
        if observer.is_alive():
            observer.stop()
            observer.join(timeout=1.0)
            
        # Remove from tracking
        del self.observers[path]
        self.watched_paths.remove(path)
        
        logger.info(f"Stopped watching path: {path}")
        return True
    
    def get_watched_directories(self) -> List[str]:
        """Get list of watched directories"""
        return list(self.watched_paths)
    
    def register_callback(self, event_type: str, callback: Callable, file_extensions: Optional[Set[str]] = None):
        """
        Register a callback for a specific file event type
        
        Args:
            event_type: Event type (file_created, file_modified, etc.)
            callback: Callback function to be called when event occurs
            file_extensions: Set of file extensions to trigger on (None for all files)
        """
        if event_type not in self.callbacks:
            logger.error(f"Invalid event type: {event_type}")
            return False
            
        self.callbacks[event_type].append({
            'func': callback,
            'extensions': file_extensions
        })
        
        logger.debug(f"Registered callback for {event_type}")
        return True
    
    def register_code_file_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for code file events
        
        Args:
            event_type: Event type (file_created, file_modified, etc.)
            callback: Callback function to be called when event occurs
        """
        return self.register_callback(event_type, callback, self.code_extensions)
    
    def trigger(self, event_type: str, *args):
        """
        Trigger callbacks for an event (internal use)
        
        Args:
            event_type: Event type
            *args: Arguments to pass to callbacks
        """
        # Add event to queue for processing
        self.event_queue.put((event_type, args))
    
    def _event_processing_loop(self):
        """Process events from the queue"""
        while self.running:
            try:
                # Get event from queue with timeout
                try:
                    event_type, args = self.event_queue.get(timeout=1.0)
                except Queue.Empty:
                    continue
                
                # Process the event
                self._process_event(event_type, args)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing file system event: {str(e)}")
    
    def _process_event(self, event_type: str, args):
        """Process a single event"""
        if event_type not in self.callbacks:
            return
            
        # Extract path from args
        path = args[0] if args else None
        if not path:
            return
            
        # Get file extension if this is a file path
        extension = None
        if os.path.isfile(path):
            extension = os.path.splitext(path)[1].lower()
        
        # Call registered callbacks
        for callback_info in self.callbacks[event_type]:
            try:
                # Check file extension if specified
                if callback_info['extensions'] is not None and extension is not None:
                    if extension not in callback_info['extensions']:
                        continue
                
                # Call callback with args
                callback_info['func'](*args)
                
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {str(e)}")

# Global instance for easy access
_file_system_watcher = FileSystemWatcher()

def get_file_system_watcher() -> FileSystemWatcher:
    """Get the global file system watcher instance"""
    global _file_system_watcher
    return _file_system_watcher

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Set up a simple callback
    def on_file_modified(path):
        print(f"File modified: {path}")
    
    # Get watcher and register callback
    watcher = get_file_system_watcher()
    watcher.register_callback('file_modified', on_file_modified)
    
    # Watch current directory
    watcher.watch_directory(".")
    
    # Start watching
    watcher.start()
    
    try:
        print("Watching current directory. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("Stopped watching")
