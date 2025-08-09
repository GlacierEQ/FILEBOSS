"""
File Organizer Module

Provides file organization capabilities including moving, copying, and renaming files
based on various criteria such as file type, creation date, etc.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from datetime import datetime
import re

from .file_analyzer import FileAnalyzer
from .file_utils import (
    get_file_type,
    calculate_file_hash,
    safe_copy,
    safe_move,
    get_file_metadata,
    is_hidden,
    format_size,
    find_files,
    get_directory_size
)

logger = logging.getLogger(__name__)

class FileOrganizer:
    """Organizes files based on various criteria and rules."""
    
    def __init__(self, dry_run: bool = False, overwrite: bool = False, 
                 include_hidden: bool = False, log_level: int = logging.INFO):
        """Initialize the file organizer.
        
        Args:
            dry_run: If True, simulate operations without making changes
            overwrite: If True, overwrite existing files when moving/copying
            include_hidden: If True, include hidden files in operations
            log_level: Logging level (default: INFO)
        """
        self.dry_run = dry_run
        self.overwrite = overwrite
        self.include_hidden = include_hidden
        self.analyzer = FileAnalyzer(include_hidden=include_hidden)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_copied': 0,
            'files_deleted': 0,
            'duplicates_found': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'total_size_processed': 0
        }
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Dict]:
        """Scan a directory and return file information.
        
        Args:
            directory: Directory to scan
            recursive: If True, scan subdirectories recursively
            
        Returns:
            List of file metadata dictionaries
        """
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist: {directory}")
            return []
            
        logger.info(f"Scanning directory: {directory}")
        
        files = []
        try:
            pattern = '**/*' if recursive else '*'
            for file_path in directory.glob(pattern):
                if file_path.is_file() and (self.include_hidden or not is_hidden(file_path)):
                    try:
                        file_info = self.analyzer.get_file_metadata(file_path)
                        if file_info:
                            files.append(file_info)
                            self.stats['files_processed'] += 1
                            self.stats['total_size_processed'] += file_info.get('size', 0)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        self.stats['errors'] += 1
            
            logger.info(f"Indexed {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            self.stats['errors'] += 1
            return []
    
    def organize_by_type(self, source_dir: Path, dest_dir: Path, 
                        copy: bool = False, pattern: str = '*', 
                        recursive: bool = True) -> Dict[str, int]:
        """Organize files by their type into subdirectories.
        
        Args:
            source_dir: Source directory to organize
            dest_dir: Destination directory for organized files
            copy: If True, copy files instead of moving them
            pattern: File pattern to match (e.g., '*.jpg')
            recursive: If True, process subdirectories recursively
            
        Returns:
            Dictionary with counts of files processed by type
        """
        if not source_dir.exists() or not source_dir.is_dir():
            logger.error(f"Source directory does not exist: {source_dir}")
            return {}
            
        if not dest_dir.exists():
            if not self.dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created destination directory: {dest_dir}")
            
        logger.info(f"Organizing files by type from {source_dir} to {dest_dir}")
        
        type_counts = {}
        files = find_files(source_dir, pattern, recursive, self.include_hidden)
        
        for file_path in files:
            try:
                file_type = get_file_type(file_path)
                if file_type not in type_counts:
                    type_counts[file_type] = 0
                type_counts[file_type] += 1
                
                # Create type directory
                type_dir = dest_dir / file_type
                if not type_dir.exists() and not self.dry_run:
                    type_dir.mkdir(parents=True, exist_ok=True)
                
                # Move or copy the file
                dest_path = type_dir / file_path.name
                self._process_file(file_path, dest_path, copy=copy)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Log results
        for file_type, count in sorted(type_counts.items()):
            logger.info(f"  {file_type}: {count} files")
            
        return type_counts
    
    def organize_by_date(self, source_dir: Path, dest_dir: Path, 
                        date_format: str = '%Y-%m-%d', copy: bool = False,
                        pattern: str = '*', recursive: bool = True) -> Dict[str, int]:
        """Organize files by their modification date.
        
        Args:
            source_dir: Source directory to organize
            dest_dir: Destination directory for organized files
            date_format: strftime format for date-based directories
            copy: If True, copy files instead of moving them
            pattern: File pattern to match
            recursive: If True, process subdirectories recursively
            
        Returns:
            Dictionary with counts of files processed by date
        """
        if not source_dir.exists() or not source_dir.is_dir():
            logger.error(f"Source directory does not exist: {source_dir}")
            return {}
            
        logger.info(f"Organizing files by date from {source_dir} to {dest_dir}")
        
        date_counts = {}
        files = find_files(source_dir, pattern, recursive, self.include_hidden)
        
        for file_path in files:
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                date_str = mtime.strftime(date_format)
                
                if date_str not in date_counts:
                    date_counts[date_str] = 0
                date_counts[date_str] += 1
                
                # Create date directory
                date_dir = dest_dir / date_str
                if not date_dir.exists() and not self.dry_run:
                    date_dir.mkdir(parents=True, exist_ok=True)
                
                # Move or copy the file
                dest_path = date_dir / file_path.name
                self._process_file(file_path, dest_path, copy=copy)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Log results
        for date_str, count in sorted(date_counts.items()):
            logger.info(f"  {date_str}: {count} files")
            
        return date_counts
    
    def find_duplicates(self, directory: Path, recursive: bool = True) -> Dict[str, List[Dict]]:
        """Find duplicate files in a directory.
        
        Args:
            directory: Directory to search for duplicates
            recursive: If True, search subdirectories recursively
            
        Returns:
            Dictionary mapping hash values to lists of duplicate files
        """
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist: {directory}")
            return {}
            
        logger.info(f"Searching for duplicate files in {directory}")
        
        # First get all files
        files = []
        pattern = '**/*' if recursive else '*'
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and (self.include_hidden or not is_hidden(file_path)):
                try:
                    file_info = self.analyzer.get_file_metadata(file_path)
                    if file_info:
                        files.append(file_info)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        # Find duplicates
        duplicates = self.analyzer.find_duplicates(files)
        
        # Log results
        if duplicates:
            logger.info(f"Found {len(duplicates)} sets of duplicate files:")
            for i, (file_hash, dup_files) in enumerate(duplicates.items(), 1):
                logger.info(f"\nSet {i} - {len(dup_files)} files (hash: {file_hash[:8]}...):")
                for dup in dup_files:
                    logger.info(f"  {dup['path']} ({format_size(dup.get('size', 0))})")
        else:
            logger.info("No duplicate files found.")
            
        self.stats['duplicates_found'] = len(duplicates)
        return duplicates
    
    def analyze_directory(self, directory: Path, recursive: bool = True) -> Dict[str, Any]:
        """Analyze directory contents and return statistics.
        
        Args:
            directory: Directory to analyze
            recursive: If True, analyze subdirectories recursively
            
        Returns:
            Dictionary containing analysis results
        """
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist: {directory}")
            return {}
            
        logger.info(f"Analyzing directory: {directory}")
        
        files = self.scan_directory(directory, recursive)
        total_size = sum(f.get('size', 0) for f in files)
        
        # Get file type distribution
        type_counts = {}
        for file_info in files:
            file_type = file_info.get('type', 'unknown')
            if file_type not in type_counts:
                type_counts[file_type] = 0
            type_counts[file_type] += 1
        
        # Get oldest and newest files
        if files:
            sorted_files = sorted(
                files,
                key=lambda x: x.get('modified', ''),
                reverse=True
            )
            newest_files = sorted_files[:5]
            oldest_files = sorted_files[-5:][::-1]
        else:
            newest_files = []
            oldest_files = []
        
        # Get largest files
        largest_files = sorted(
            [f for f in files if 'size' in f],
            key=lambda x: x.get('size', 0),
            reverse=True
        )[:5]
        
        # Get directory size
        dir_size, file_count = get_directory_size(directory)
        
        # Prepare results
        results = {
            'directory': str(directory.absolute()),
            'file_count': len(files),
            'total_size': total_size,
            'total_size_formatted': format_size(total_size),
            'type_distribution': type_counts,
            'newest_files': newest_files,
            'oldest_files': oldest_files,
            'largest_files': largest_files,
            'directory_size': dir_size,
            'directory_size_formatted': format_size(dir_size),
            'directory_file_count': file_count,
            'scan_time': datetime.now().isoformat(),
            'include_hidden': self.include_hidden,
            'recursive': recursive
        }
        
        # Log summary
        logger.info(f"\n=== Directory Analysis ===")
        logger.info(f"Location: {directory}")
        logger.info(f"Total files: {len(files):,}")
        logger.info(f"Total size: {format_size(total_size)}")
        logger.info("\nFile types:")
        for file_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {file_type}: {count}")
        
        return results
    
    def _process_file(self, source_path: Path, dest_path: Path, copy: bool = False) -> bool:
        """Process a file (move or copy) with error handling.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            copy: If True, copy the file; otherwise move it
            
        Returns:
            True if successful, False otherwise
        """
        if not source_path.exists() or not source_path.is_file():
            logger.error(f"Source file does not exist: {source_path}")
            self.stats['errors'] += 1
            return False
            
        if dest_path.exists():
            if not self.overwrite:
                logger.warning(f"Destination already exists, skipping (use --overwrite): {dest_path}")
                return False
            elif not self.dry_run:
                try:
                    dest_path.unlink()
                except OSError as e:
                    logger.error(f"Error removing existing file {dest_path}: {e}")
                    self.stats['errors'] += 1
                    return False
        
        # Perform the operation
        try:
            if self.dry_run:
                logger.info(f"{'Would copy' if copy else 'Would move'} {source_path} to {dest_path}")
                result = True
            else:
                if copy:
                    result = safe_copy(source_path, dest_path)
                    if result:
                        self.stats['files_copied'] += 1
                else:
                    result = safe_move(source_path, dest_path)
                    if result:
                        self.stats['files_moved'] += 1
            
            if not result:
                self.stats['errors'] += 1
                
            return result
            
        except Exception as e:
            logger.error(f"Error {'copying' if copy else 'moving'} {source_path} to {dest_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the operations performed.
        
        Returns:
            Dictionary containing operation statistics
        """
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        stats = {
            'files_processed': self.stats['files_processed'],
            'files_moved': self.stats['files_moved'],
            'files_copied': self.stats['files_copied'],
            'files_deleted': self.stats['files_deleted'],
            'duplicates_found': self.stats['duplicates_found'],
            'errors': self.stats['errors'],
            'start_time': self.stats['start_time'].isoformat(),
            'end_time': self.stats['end_time'].isoformat(),
            'duration_seconds': round(duration, 2),
            'dry_run': self.dry_run,
            'include_hidden': self.include_hidden
        }
        
        if self.stats['files_processed'] > 0:
            files_per_second = self.stats['files_processed'] / duration if duration > 0 else 0
            stats['files_per_second'] = round(files_per_second, 2)
            
            if 'total_size_processed' in self.stats and self.stats['total_size_processed'] > 0:
                total_size_gb = self.stats['total_size_processed'] / (1024 ** 3)
                stats['total_size_processed'] = self.stats['total_size_processed']
                stats['total_size_processed_formatted'] = format_size(self.stats['total_size_processed'])
                stats['throughput_mb_per_second'] = round((self.stats['total_size_processed'] / (1024 * 1024)) / duration, 2) if duration > 0 else 0
        
        return stats
