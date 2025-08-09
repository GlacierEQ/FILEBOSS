"""
File Analyzer Module

Provides file analysis capabilities including metadata extraction,
duplicate detection, and file type classification.
"""

import hashlib
import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FileAnalyzer:
    """Analyzes files for metadata, types, and duplicates."""
    
    def __init__(self, include_hidden: bool = False):
        """Initialize the file analyzer.
        
        Args:
            include_hidden: Whether to include hidden files in analysis
        """
        self.include_hidden = include_hidden
        self._init_mime_types()
    
    def _init_mime_types(self) -> None:
        """Initialize custom MIME type mappings."""
        # Add custom MIME type mappings
        mimetypes.add_type('application/x-ipynb', '.ipynb')
        mimetypes.add_type('application/x-msdos-program', '.exe')
        mimetypes.add_type('application/x-msi', '.msi')
    
    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from a file.
        
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
                'is_hidden': self._is_hidden(file_path),
                'hash_md5': self._calculate_hash(file_path, 'md5'),
                'hash_sha256': self._calculate_hash(file_path, 'sha256'),
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return {}
    
    def _is_hidden(self, path: Path) -> bool:
        """Check if a file is hidden."""
        if path.name.startswith('.'):
            return True
        if hasattr(path, 'is_hidden') and path.is_hidden():
            return True
        return False
    
    def _calculate_hash(self, file_path: Path, algorithm: str = 'sha256', 
                       chunk_size: int = 8192) -> Optional[str]:
        """Calculate file hash using specified algorithm."""
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
    
    def find_duplicates(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Find duplicate files based on size and hash.
        
        Args:
            files: List of file metadata dictionaries
            
        Returns:
            Dictionary mapping hash values to lists of duplicate files
        """
        # First group by size (fast check)
        size_groups: Dict[int, List[Dict]] = {}
        for file_info in files:
            size = file_info.get('size', 0)
            if size not in size_groups:
                size_groups[size] = []
            size_groups[size].append(file_info)
        
        # Then check hashes for files with same size
        hash_groups: Dict[str, List[Dict]] = {}
        for size, file_group in size_groups.items():
            if len(file_group) > 1:  # Potential duplicates
                for file_info in file_group:
                    file_hash = file_info.get('hash_sha256')
                    if not file_hash:
                        continue
                    
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file_info)
        
        # Only return groups with actual duplicates
        return {h: group for h, group in hash_groups.items() if len(group) > 1}
    
    def analyze_file_types(self, files: List[Dict]) -> Dict[str, int]:
        """Analyze distribution of file types.
        
        Args:
            files: List of file metadata dictionaries
            
        Returns:
            Dictionary mapping file types to counts
        """
        type_counts: Dict[str, int] = {}
        
        for file_info in files:
            mime_type = file_info.get('mime_type', 'unknown').split('/')[0]
            if mime_type not in type_counts:
                type_counts[mime_type] = 0
            type_counts[mime_type] += 1
            
        return type_counts
    
    def get_oldest_newest_files(self, files: List[Dict], count: int = 5) -> Dict[str, List[Dict]]:
        """Get oldest and newest files by modification time.
        
        Args:
            files: List of file metadata dictionaries
            count: Number of files to return for each category
            
        Returns:
            Dictionary with 'oldest' and 'newest' file lists
        """
        if not files:
            return {'oldest': [], 'newest': []}
            
        # Sort by modification time
        sorted_files = sorted(
            files,
            key=lambda x: datetime.fromisoformat(x.get('modified', '1970-01-01T00:00:00')),
            reverse=False
        )
        
        return {
            'oldest': sorted_files[:count],
            'newest': sorted_files[-count:][::-1]  # Newest first
        }
