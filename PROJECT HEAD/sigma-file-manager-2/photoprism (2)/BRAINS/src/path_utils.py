"""
Path utilities for Sorting Hat

This module provides utilities for path validation, safety checks,
and common path operations.
"""
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

from src.config import config, get_safe_path
from src.error_handler import PathError, get_logger, safe_path_operation

# Get logger
logger = get_logger(__name__)

class SafePath:
    """Utility class for safe path operations"""
    
    # Patterns for unsafe paths
    UNSAFE_PATTERNS = [
        r"(^|/)\.git(/|$)",  # Git repositories
        r"(^|/)node_modules(/|$)",  # Node.js modules
        r"(^|/)__pycache__(/|$)",  # Python cache
        r"(^|/)venv(/|$)",  # Python virtual environments
        r"(^|/)\.env(/|$)",  # Environment files
    ]
    
    # System folders to protect
    SYSTEM_FOLDERS = config.get("ignore_folders", [])
    
    @staticmethod
    def is_safe_path(path: Union[str, Path]) -> bool:
        """
        Check if a path is safe to operate on
        
        Args:
            path: Path to check
            
        Returns:
            True if the path is safe, False otherwise
        """
        if not path:
            return False
            
        # Convert to string if it's a Path object
        path_str = str(path).lower()
        
        # Check for GitHub repositories
        if "github" in path_str:
            logger.warning(f"Skipping GitHub path: {path}")
            return False
            
        # Check for unsafe patterns
        for pattern in SafePath.UNSAFE_PATTERNS:
            if re.search(pattern, path_str, re.IGNORECASE):
                logger.warning(f"Skipping unsafe path matching pattern {pattern}: {path}")
                return False
                
        # Check for system folders
        for folder in SafePath.SYSTEM_FOLDERS:
            if folder.lower() in path_str.lower():
                logger.warning(f"Skipping system folder: {path}")
                return False
                
        return True
    
    @staticmethod
    def get_safe_path(path: Optional[Union[str, Path]] = None) -> str:
        """
        Get a safe path for file operations
        
        Args:
            path: Optional path to validate
            
        Returns:
            Safe path to use
            
        Raises:
            PathError: If the path is not safe
        """
        # If no path provided, use the default safe path
        if not path:
            default_path = get_safe_path()
            os.makedirs(default_path, exist_ok=True)
            return default_path
            
        # Convert to string if it's a Path object
        path_str = str(path)
        
        # Check if the path is safe
        if not SafePath.is_safe_path(path_str):
            raise PathError(
                message=f"Path is not safe for operations: {path_str}",
                path=path_str
            )
            
        # Check if the path exists
        if not os.path.exists(path_str):
            # Try to create the directory
            try:
                os.makedirs(path_str, exist_ok=True)
                logger.info(f"Created directory: {path_str}")
            except Exception as e:
                logger.error(f"Failed to create directory {path_str}: {e}")
                # Fall back to default safe path
                default_path = get_safe_path()
                os.makedirs(default_path, exist_ok=True)
                return default_path
                
        return path_str
    
    @staticmethod
    def is_path_writable(path: Union[str, Path]) -> bool:
        """
        Check if a path is writable
        
        Args:
            path: Path to check
            
        Returns:
            True if the path is writable, False otherwise
        """
        if not os.path.exists(path):
            # Check if parent directory is writable
            parent = os.path.dirname(path)
            if not parent:  # Handle case where path is just a filename
                parent = "."
            return os.access(parent, os.W_OK)
        else:
            return os.access(path, os.W_OK)
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> str:
        """
        Normalize a path for consistent comparison
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path string
        """
        return os.path.normpath(str(path)).lower()
    
    @staticmethod
    def is_subpath(path: Union[str, Path], parent: Union[str, Path]) -> bool:
        """
        Check if a path is a subpath of another path
        
        Args:
            path: Path to check
            parent: Parent path
            
        Returns:
            True if path is a subpath of parent, False otherwise
        """
        path_norm = SafePath.normalize_path(path)
        parent_norm = SafePath.normalize_path(parent)
        
        return path_norm.startswith(parent_norm)
    
    @staticmethod
    def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> str:
        """
        Get the relative path from a base path
        
        Args:
            path: Path to get relative path for
            base: Base path
            
        Returns:
            Relative path
        """
        return os.path.relpath(str(path), str(base))
    
    @staticmethod
    @safe_path_operation(operation_name="copy file")
    def safe_copy(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """
        Safely copy a file
        
        Args:
            src: Source path
            dst: Destination path
            
        Raises:
            FileOperationError: If the copy operation fails
        """
        # Validate paths
        if not SafePath.is_safe_path(src) or not SafePath.is_safe_path(dst):
            raise PathError(
                message="Cannot copy from/to unsafe path",
                path=f"{src} -> {dst}"
            )
            
        # Create destination directory if it doesn't exist
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)
        
        # Copy the file
        shutil.copy2(src, dst)
        logger.info(f"Copied file: {src} -> {dst}")
    
    @staticmethod
    @safe_path_operation(operation_name="move file")
    def safe_move(src: Union[str, Path], dst: Union[str, Path]) -> None:
        """
        Safely move a file
        
        Args:
            src: Source path
            dst: Destination path
            
        Raises:
            FileOperationError: If the move operation fails
        """
        # Validate paths
        if not SafePath.is_safe_path(src) or not SafePath.is_safe_path(dst):
            raise PathError(
                message="Cannot move from/to unsafe path",
                path=f"{src} -> {dst}"
            )
            
        # Create destination directory if it doesn't exist
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)
        
        # Move the file
        shutil.move(src, dst)
        logger.info(f"Moved file: {src} -> {dst}")
    
    @staticmethod
    @safe_path_operation(operation_name="delete file")
    def safe_delete(path: Union[str, Path]) -> None:
        """
        Safely delete a file
        
        Args:
            path: Path to delete
            
        Raises:
            FileOperationError: If the delete operation fails
        """
        # Validate path
        if not SafePath.is_safe_path(path):
            raise PathError(
                message="Cannot delete unsafe path",
                path=str(path)
            )
            
        # Delete the file or directory
        if os.path.isdir(path):
            shutil.rmtree(path)
            logger.info(f"Deleted directory: {path}")
        else:
            os.remove(path)
            logger.info(f"Deleted file: {path}")
    
    @staticmethod
    def get_unique_path(path: Union[str, Path]) -> str:
        """
        Get a unique path by appending a counter if the path already exists
        
        Args:
            path: Original path
            
        Returns:
            Unique path
        """
        if not os.path.exists(path):
            return str(path)
            
        base, ext = os.path.splitext(path)
        counter = 1
        
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
            
        return f"{base}_{counter}{ext}"
    
    @staticmethod
    def is_binary_file(path: Union[str, Path]) -> bool:
        """
        Check if a file is binary
        
        Args:
            path: Path to check
            
        Returns:
            True if the file is binary, False otherwise
        """
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return True  # Assume binary if we can't read the file
