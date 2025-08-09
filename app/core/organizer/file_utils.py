"""
File Utility Functions

Provides helper functions for file operations, type detection, and metadata handling.
"""

import hashlib
import logging
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Callable, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

def get_file_type(file_path: Path) -> str:
    """Determine the general type of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        String representing the file type category
    """
    if not file_path.is_file():
        return 'unknown'
    
    ext = file_path.suffix.lower()
    
    # Document types
    if ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.md', '.markdown']:
        return 'document'
    # Spreadsheet types
    elif ext in ['.xls', '.xlsx', '.csv', '.ods', '.tsv']:
        return 'spreadsheet'
    # Presentation types
    elif ext in ['.ppt', '.pptx', '.odp', '.key']:
        return 'presentation'
    # Image types
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.heic', '.heif']:
        return 'image'
    # Video types
    elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.mpeg', '.mpg']:
        return 'video'
    # Audio types
    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus']:
        return 'audio'
    # Archive types
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.z', '.lzma']:
        return 'archive'
    # Code types
    elif ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', 
                '.rs', '.rb', '.php', '.html', '.css', '.scss', '.less', '.json', '.xml', '.yaml', 
                '.yml', '.toml', '.ini', '.sh', '.bat', '.ps1', '.cmd', '.sql']:
        return 'code'
    # E-book types
    elif ext in ['.epub', '.mobi', '.azw3', '.cbz', '.cbr', '.djvu']:
        return 'ebook'
    # Database files
    elif ext in ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.frm', '.myd', '.myi']:
        return 'database'
    # Virtual machine/disk images
    elif ext in ['.iso', '.vdi', '.vmdk', '.vhd', '.vhdx']:
        return 'disk_image'
    # Font files
    elif ext in ['.ttf', '.otf', '.woff', '.woff2', '.eot']:
        return 'font'
    # Configuration files
    elif ext in ['.conf', '.cfg', '.config', '.properties', '.env']:
        return 'config'
    # Log files
    elif ext in ['.log', '.txt']:
        return 'log'
    # Executable files
    elif ext in ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage']:
        return 'executable'
    # Virtual environment
    elif file_path.name in ['__pycache__', 'venv', 'env', '.venv', 'virtualenv', '.virtualenv']:
        return 'virtualenv'
    # Version control
    elif file_path.name in ['.git', '.svn', '.hg']:
        return 'vcs'
    # Common hidden files
    elif file_path.name.startswith('.') or file_path.name.startswith('~'):
        return 'hidden'
    else:
        return 'other'

def calculate_file_hash(file_path: Path, algorithm: str = 'sha256', 
                      chunk_size: int = 8192) -> Optional[str]:
    """Calculate the hash of a file's contents.
    
    Args:
        file_path: Path to the file
        algorithm: Hashing algorithm to use (default: 'sha256')
        chunk_size: Size of chunks to read at once (bytes)
        
    Returns:
        Hex digest of the file's hash, or None if an error occurs
    """
    if algorithm not in hashlib.algorithms_available:
        logger.warning(f"Hash algorithm {algorithm} not available")
        return None
        
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (IOError, OSError) as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None

def safe_copy(src: Path, dest: Path) -> bool:
    """Safely copy a file, creating parent directories if needed.
    
    Args:
        src: Source file path
        dest: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error copying {src} to {dest}: {e}")
        return False

def safe_move(src: Path, dest: Path) -> bool:
    """Safely move a file, creating parent directories if needed.
    
    Args:
        src: Source file path
        dest: Destination file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        return True
    except (IOError, OSError) as e:
        logger.error(f"Error moving {src} to {dest}: {e}")
        return False

def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Get basic metadata about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file metadata
    """
    try:
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            'path': str(file_path.absolute()),
            'name': file_path.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
            'mime_type': mime_type or 'application/octet-stream',
            'extension': file_path.suffix.lower(),
            'is_hidden': is_hidden(file_path),
            'type': get_file_type(file_path),
        }
    except Exception as e:
        logger.error(f"Error getting metadata for {file_path}: {e}")
        return {}

def is_hidden(path: Path) -> bool:
    """Check if a file or directory is hidden.
    
    Args:
        path: Path to check
        
    Returns:
        True if the path is hidden, False otherwise
    """
    # Check for dot-prefixed files (Unix-like hidden)
    if path.name.startswith('.'):
        return True
        
    # Check for hidden attribute on Windows
    if os.name == 'nt':
        try:
            import ctypes
            # FILE_ATTRIBUTE_HIDDEN = 0x2
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path.absolute()))
            return attrs != 0xFFFFFFFF and bool(attrs & 0x2)
        except (ImportError, AttributeError, OSError):
            pass
            
    # Check for hidden attribute on Unix-like systems
    try:
        return bool(os.stat(path).st_file_attributes & 0x4000)  # UF_HIDDEN
    except (AttributeError, OSError):
        pass
        
    return False

def get_directory_size(path: Path) -> Tuple[int, int]:
    """Calculate the total size and file count of a directory.
    
    Args:
        path: Directory path
        
    Returns:
        Tuple of (total_size_in_bytes, file_count)
    """
    total_size = 0
    file_count = 0
    
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
        
    return total_size, file_count

def format_size(size_in_bytes: int, precision: int = 2) -> str:
    """Format a size in bytes to a human-readable string.
    
    Args:
        size_in_bytes: Size in bytes
        precision: Number of decimal places to show
        
    Returns:
        Formatted size string (e.g., "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.{precision}f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.{precision}f} PB"

def find_files(directory: Path, pattern: str = '*', 
              recursive: bool = True, include_hidden: bool = False) -> List[Path]:
    """Find files matching a pattern in a directory.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern to match (default: '*')
        recursive: Whether to search recursively
        include_hidden: Whether to include hidden files/directories
        
    Returns:
        List of matching file paths
    """
    if not directory.is_dir():
        return []
        
    try:
        if recursive:
            gen = directory.rglob(pattern)
        else:
            gen = directory.glob(pattern)
            
        return [
            path for path in gen 
            if path.is_file() and (include_hidden or not is_hidden(path))
        ]
    except (OSError, PermissionError) as e:
        logger.error(f"Error finding files in {directory}: {e}")
        return []
