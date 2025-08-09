"""
Watch Service

This module provides functionality to monitor directories for new or modified files
and automatically process them using the file organizer.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .file_organizer import FileOrganizer
from .database import DatabaseService
from ..models import File
from ..schemas import FileCreate, FileCategory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileEventHandler(FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(
        self, 
        db_service: DatabaseService,
        organizer: FileOrganizer,
        case_id: str,
        subcase_id: Optional[str] = None,
        category: Optional[FileCategory] = None,
        recursive: bool = True
    ):
        """Initialize the file event handler.
        
        Args:
            db_service: Database service instance
            organizer: File organizer instance
            case_id: ID of the case to associate with processed files
            subcase_id: Optional ID of the subcase
            category: Default category for processed files
            recursive: Whether to process subdirectories recursively
        """
        self.db_service = db_service
        self.organizer = organizer
        self.case_id = case_id
        self.subcase_id = subcase_id
        self.category = category or FileCategory.OTHER
        self.recursive = recursive
        self._processed_files: Set[str] = set()
        
        # Load already processed files to avoid reprocessing
        self._load_processed_files()
    
    def _load_processed_files(self) -> None:
        """Load already processed files from the database."""
        try:
            # Get all files for this watch configuration
            files = self.db_service.get_files_by_case(
                case_id=self.case_id,
                subcase_id=self.subcase_id
            )
            self._processed_files = {f.stored_path for f in files}
            logger.info(f"Loaded {len(self._processed_files)} processed files from database")
        except Exception as e:
            logger.error(f"Error loading processed files: {e}")
            self._processed_files = set()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Called when a file or directory is created."""
        if event.is_directory:
            if self.recursive:
                # Process all files in the new directory
                self._process_directory(event.src_path)
            return
        
        # Process the new file
        self._process_file(event.src_path)
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Called when a file or directory is modified."""
        if event.is_directory:
            return
        
        # Process the modified file
        self._process_file(event.src_path)
    
    def _process_file(self, file_path: str) -> None:
        """Process a single file."""
        try:
            # Skip if already processed
            if file_path in self._processed_files:
                return
            
            # Skip temporary files
            if self._is_temporary_file(file_path):
                logger.debug(f"Skipping temporary file: {file_path}")
                return
            
            logger.info(f"Processing new/modified file: {file_path}")
            
            # Organize the file
            result = self.organizer.organize_file(
                file_path=file_path,
                case_id=self.case_id,
                subcase_id=self.subcase_id,
                category=self.category
            )
            
            if not result or not result.get('success'):
                logger.error(f"Failed to organize file: {file_path}")
                return
            
            # Mark as processed
            self._processed_files.add(file_path)
            logger.info(f"Successfully processed file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def _process_directory(self, directory: str) -> None:
        """Process all files in a directory."""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return
            
            # Process all files in the directory
            for file_path in path.glob('**/*' if self.recursive else '*'):
                if file_path.is_file():
                    self._process_file(str(file_path))
        except Exception as e:
            logger.error(f"Error processing directory {directory}: {e}")
    
    @staticmethod
    def _is_temporary_file(file_path: str) -> bool:
        """Check if a file is a temporary file that should be ignored."""
        temp_extensions = {
            '.tmp', '.temp', '~', '.swp', '.swpx', '.swx', '.part',
            '.crdownload', '.download', '.partial', '.part', '.tmp',
            '.temp', '.wbk', '.xlk', '.bak', '.backup'
        }
        
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext in temp_extensions:
            return True
        
        # Check for temporary file patterns in the name
        temp_patterns = {'~$', '~'}
        filename = os.path.basename(file_path)
        if any(pattern in filename for pattern in temp_patterns):
            return True
        
        return False


class WatchService:
    """Service for monitoring directories and processing new files."""
    
    def __init__(self, db_service: DatabaseService, organizer: FileOrganizer):
        """Initialize the watch service."""
        self.db_service = db_service
        self.organizer = organizer
        self.observer = Observer()
        self.watches: Dict[str, FileEventHandler] = {}
    
    def start(self) -> None:
        """Start the watch service."""
        if not self.observer.is_alive():
            self.observer.start()
            logger.info("Watch service started")
    
    def stop(self) -> None:
        """Stop the watch service."""
        self.observer.stop()
        self.observer.join()
        self.watches.clear()
        logger.info("Watch service stopped")
    
    def add_watch(
        self,
        directory: str,
        case_id: str,
        subcase_id: Optional[str] = None,
        category: Optional[FileCategory] = None,
        recursive: bool = True
    ) -> bool:
        """Add a directory to watch.
        
        Args:
            directory: Path to the directory to watch
            case_id: ID of the case to associate with processed files
            subcase_id: Optional ID of the subcase
            category: Default category for processed files
            recursive: Whether to watch subdirectories
            
        Returns:
            bool: True if watch was added successfully, False otherwise
        """
        try:
            # Convert to absolute path and normalize
            directory = os.path.abspath(directory)
            
            # Check if already watching this directory
            if directory in self.watches:
                logger.warning(f"Already watching directory: {directory}")
                return False
            
            # Ensure directory exists
            if not os.path.isdir(directory):
                logger.error(f"Directory does not exist: {directory}")
                return False
            
            # Create event handler
            handler = FileEventHandler(
                db_service=self.db_service,
                organizer=self.organizer,
                case_id=case_id,
                subcase_id=subcase_id,
                category=category,
                recursive=recursive
            )
            
            # Schedule the watch
            self.observer.schedule(
                handler,
                directory,
                recursive=recursive
            )
            
            # Store the handler
            self.watches[directory] = {
                'handler': handler,
                'case_id': case_id,
                'subcase_id': subcase_id,
                'category': category,
                'recursive': recursive
            }
            
            logger.info(f"Added watch for directory: {directory} (case: {case_id})")
            
            # Process any existing files in the directory
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        handler._process_file(file_path)
            else:
                for entry in os.scandir(directory):
                    if entry.is_file():
                        handler._process_file(entry.path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding watch for {directory}: {e}")
            return False
    
    def remove_watch(self, directory: str) -> bool:
        """Remove a directory watch.
        
        Args:
            directory: Path to the directory being watched
            
        Returns:
            bool: True if watch was removed, False if not found
        """
        directory = os.path.abspath(directory)
        
        if directory not in self.watches:
            logger.warning(f"No active watch for directory: {directory}")
            return False
        
        # Stop watching the directory
        for watch in self.observer._handlers.get(directory, []):
            self.observer.unschedule(watch)
        
        # Remove from our tracking
        del self.watches[directory]
        
        logger.info(f"Removed watch for directory: {directory}")
        return True
    
    def list_watches(self) -> List[Dict[str, Any]]:
        """Get information about all active watches.
        
        Returns:
            List of dictionaries containing watch information
        """
        return [
            {
                'directory': dir_path,
                'case_id': info['case_id'],
                'subcase_id': info['subcase_id'],
                'category': info['category'].value if info['category'] else None,
                'recursive': info['recursive']
            }
            for dir_path, info in self.watches.items()
        ]
    
    def is_watching(self, directory: str) -> bool:
        """Check if a directory is being watched.
        
        Args:
            directory: Path to the directory to check
            
        Returns:
            bool: True if the directory is being watched, False otherwise
        """
        return os.path.abspath(directory) in self.watches
