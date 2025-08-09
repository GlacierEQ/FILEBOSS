"""
File Organizer and Analyzer Module

This module provides advanced file organization and analysis capabilities.
It can scan directories, analyze file contents, and organize files based on
custom rules and patterns.
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Class to hold file metadata and analysis results."""
    path: Path
    size: int
    created: datetime
    modified: datetime
    file_type: str
    mime_type: str
    extension: str
    md5_hash: str = ""
    sha256_hash: str = ""
    tags: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)

class FileOrganizer:
    """
    Advanced file organizer and analyzer that can process and organize files
    based on various criteria including file type, content, and metadata.
    """
    
    def __init__(self, root_dir: Union[str, Path] = "."):
        """Initialize the file organizer with a root directory.
        
        Args:
            root_dir: The root directory to organize
        """
        self.root_dir = Path(root_dir).resolve()
        self.file_index: Dict[Path, FileInfo] = {}
        self.duplicates: Dict[str, List[Path]] = {}
        self._setup_mime_types()
    
    def _setup_mime_types(self) -> None:
        """Initialize additional MIME types for better file type detection."""
        # Add custom MIME type mappings
        mimetypes.add_type('application/zip', '.cbz')
        mimetypes.add_type('application/zip', '.cbr')
        mimetypes.add_type('application/x-rar', '.cbr')
        mimetypes.add_type('application/x-rar', '.cbr')
        mimetypes.add_type('application/epub+zip', '.epub')
        mimetypes.add_type('application/x-mobipocket-ebook', '.mobi')
        mimetypes.add_type('application/x-pdf', '.pdf')
    
    def scan_directory(self, recursive: bool = True) -> None:
        """Scan the root directory and index all files.
        
        Args:
            recursive: If True, scan subdirectories recursively
        """
        logger.info(f"Scanning directory: {self.root_dir}")
        
        if recursive:
            iterator = self.root_dir.rglob('*')
        else:
            iterator = self.root_dir.glob('*')
        
        for item in iterator:
            if item.is_file() and not item.name.startswith('.'):
                try:
                    file_info = self._get_file_info(item)
                    self.file_index[item] = file_info
                except Exception as e:
                    logger.error(f"Error processing {item}: {str(e)}")
        
        logger.info(f"Indexed {len(self.file_index)} files")
    
    def _get_file_info(self, file_path: Path) -> FileInfo:
        """Extract file information and metadata.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            FileInfo object containing file metadata
        """
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return FileInfo(
            path=file_path,
            size=stat.st_size,
            created=datetime.fromtimestamp(stat.st_ctime),
            modified=datetime.fromtimestamp(stat.st_mtime),
            file_type=self._get_file_type(file_path),
            mime_type=mime_type or 'application/octet-stream',
            extension=file_path.suffix.lower(),
            md5_hash=self._calculate_hash(file_path, 'md5'),
            sha256_hash=self._calculate_hash(file_path, 'sha256')
        )
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension and content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            String representing the file type
        """
        # TODO: Implement more sophisticated file type detection
        if file_path.suffix.lower() in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
            return 'document'
        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            return 'image'
        elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']:
            return 'video'
        elif file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            return 'audio'
        elif file_path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return 'archive'
        else:
            return 'other'
    
    def _calculate_hash(self, file_path: Path, algorithm: str = 'md5', chunk_size: int = 8192) -> str:
        """Calculate file hash using specified algorithm.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use ('md5' or 'sha256')
            chunk_size: Size of chunks to read at once
            
        Returns:
            Hexadecimal digest of the file
        """
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating {algorithm} hash for {file_path}: {str(e)}")
            return ""
    
    def find_duplicates(self) -> Dict[str, List[Path]]:
        """Find duplicate files based on their content hashes.
        
        Returns:
            Dictionary mapping file hashes to lists of duplicate file paths
        """
        hash_map: Dict[str, List[Path]] = {}
        
        for file_path, file_info in self.file_index.items():
            if file_info.sha256_hash:  # Only consider files with valid hashes
                if file_info.sha256_hash not in hash_map:
                    hash_map[file_info.sha256_hash] = []
                hash_map[file_info.sha256_hash].append(file_path)
        
        # Filter out non-duplicates
        self.duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
        return self.duplicates
    
    def organize_by_type(self, output_dir: Union[str, Path]) -> Dict[str, int]:
        """Organize files into subdirectories based on their types.
        
        Args:
            output_dir: Base directory to create type-based subdirectories in
            
        Returns:
            Dictionary mapping file types to counts of organized files
        """
        output_path = Path(output_dir)
        type_counts: Dict[str, int] = {}
        
        for file_path, file_info in self.file_index.items():
            try:
                # Create type directory if it doesn't exist
                type_dir = output_path / file_info.file_type
                type_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file to type directory
                dest_path = type_dir / file_path.name
                if file_path != dest_path:  # Avoid moving to same location
                    shutil.move(str(file_path), str(dest_path))
                    
                    # Update counts
                    type_counts[file_info.file_type] = type_counts.get(file_info.file_type, 0) + 1
            except Exception as e:
                logger.error(f"Error organizing {file_path}: {str(e)}")
        
        return type_counts
    
    def analyze_file_usage(self) -> Dict[str, int]:
        """Analyze file usage patterns.
        
        Returns:
            Dictionary with analysis results
        """
        now = datetime.now()
        analysis = {
            'total_files': len(self.file_index),
            'total_size_gb': sum(fi.size for fi in self.file_index.values()) / (1024 ** 3),
            'file_types': {},
            'last_modified': {},
            'duplicate_files': sum(len(paths) for paths in self.duplicates.values())
        }
        
        # Count files by type
        for file_info in self.file_index.values():
            # Update type counts
            analysis['file_types'][file_info.file_type] = \
                analysis['file_types'].get(file_info.file_type, 0) + 1
            
            # Track last modified times
            days_old = (now - file_info.modified).days
            if days_old < 30:
                analysis['last_modified']['< 30 days'] = analysis['last_modified'].get('< 30 days', 0) + 1
            elif days_old < 90:
                analysis['last_modified']['30-90 days'] = analysis['last_modified'].get('30-90 days', 0) + 1
            elif days_old < 365:
                analysis['last_modified']['90-365 days'] = analysis['last_modified'].get('90-365 days', 0) + 1
            else:
                analysis['last_modified']['> 1 year'] = analysis['last_modified'].get('> 1 year', 0) + 1
        
        return analysis

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FileBoss - Advanced File Organizer and Analyzer")
    parser.add_argument("directory", help="Directory to organize and analyze")
    parser.add_argument("--organize", action="store_true", help="Organize files by type")
    parser.add_argument("--find-duplicates", action="store_true", help="Find duplicate files")
    parser.add_argument("--output-dir", default="./organized", help="Output directory for organized files")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize and run the organizer
    organizer = FileOrganizer(args.directory)
    organizer.scan_directory()
    
    if args.find_duplicates:
        duplicates = organizer.find_duplicates()
        print(f"\nFound {len(duplicates)} sets of duplicate files:")
        for file_hash, paths in duplicates.items():
            print(f"\nHash: {file_hash[:8]}...")
            for path in paths:
                print(f"  - {path}")
    
    if args.organize:
        print(f"\nOrganizing files by type into: {args.output_dir}")
        type_counts = organizer.organize_by_type(args.output_dir)
        print("\nFiles organized by type:")
        for file_type, count in sorted(type_counts.items()):
            print(f"  {file_type}: {count} files")
    
    # Always show analysis
    print("\nFile Analysis:")
    analysis = organizer.analyze_file_usage()
    print(f"Total files: {analysis['total_files']}")
    print(f"Total size: {analysis['total_size_gb']:.2f} GB")
    print("\nFiles by type:")
    for file_type, count in sorted(analysis['file_types'].items()):
        print(f"  {file_type}: {count} files")
    
    print("\nLast modified:")
    for period, count in analysis['last_modified'].items():
        print(f"  {period}: {count} files")
    
    if analysis['duplicate_files'] > 0:
        print(f"\nFound {analysis['duplicate_files']} duplicate files (in {len(organizer.duplicates)} sets)")
