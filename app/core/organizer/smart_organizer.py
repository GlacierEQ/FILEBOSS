"""
Smart File Organizer

Provides intelligent file organization and renaming based on categories and case rules.
"""

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class NamingRules:
    """Rules for file naming and organization."""
    # Case styles
    CASE_LOWER = 'lower'
    CASE_UPPER = 'upper'
    CASE_TITLE = 'title'
    CASE_SENTENCE = 'sentence'
    
    # Word separators
    SEPARATOR_SPACE = 'space'
    SEPARATOR_UNDERSCORE = 'underscore'
    SEPARATOR_HYPHEN = 'hyphen'
    
    # Default settings
    case_style: str = CASE_TITLE
    word_separator: str = SEPARATOR_SPACE
    remove_special_chars: bool = True
    replace_whitespace: bool = True
    max_length: int = 64
    preserve_extension: bool = True
    
    # Custom replacements for special characters
    special_char_replacements: Dict[str, str] = field(default_factory=lambda: {
        '&': 'and',
        '@': 'at',
        '%': 'percent',
        '#': 'number',
        '+': 'plus'
    })

@dataclass
class CategoryRule:
    """Rules for categorizing files."""
    name: str
    patterns: List[str]  # List of glob patterns to match
    target_dir: str  # Relative to base directory
    naming_rules: NamingRules = field(default_factory=NamingRules)

class SmartFileOrganizer:
    """Organizes and renames files based on categories and naming rules."""
    
    def __init__(self, base_dir: Path, dry_run: bool = False, 
                 overwrite: bool = False, log_level: int = logging.INFO):
        """Initialize the smart file organizer.
        
        Args:
            base_dir: Base directory for organization
            dry_run: If True, simulate operations without making changes
            overwrite: If True, overwrite existing files
            log_level: Logging level
        """
        self.base_dir = Path(base_dir).resolve()
        self.dry_run = dry_run
        self.overwrite = overwrite
        self.categories: List[CategoryRule] = []
        self.default_naming = NamingRules()
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_renamed': 0,
            'files_skipped': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'processed_size': 0
        }
    
    def add_category(self, name: str, patterns: List[str], 
                    target_dir: str, naming_rules: Optional[NamingRules] = None) -> None:
        """Add a file category with its rules.
        
        Args:
            name: Category name
            patterns: List of glob patterns to match files
            target_dir: Target directory (relative to base_dir)
            naming_rules: Optional naming rules for this category
        """
        self.categories.append(CategoryRule(
            name=name,
            patterns=patterns,
            target_dir=target_dir,
            naming_rules=naming_rules or NamingRules()
        ))
    
    def normalize_name(self, name: str, rules: NamingRules) -> str:
        """Normalize a filename according to the specified rules.
        
        Args:
            name: Original filename (without extension)
            rules: Naming rules to apply
            
        Returns:
            Normalized filename
        """
        # Remove extension if present
        if '.' in name and not name.startswith('.'):
            name = name.rsplit('.', 1)[0]
        
        # Convert to ASCII, replacing special characters
        if rules.remove_special_chars:
            name = ''.join(c if c.isalnum() or c.isspace() 
                         else rules.special_char_replacements.get(c, '') 
                         for c in name)
        
        # Normalize unicode characters
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        
        # Apply case style
        if rules.case_style == NamingRules.CASE_LOWER:
            name = name.lower()
        elif rules.case_style == NamingRules.CASE_UPPER:
            name = name.upper()
        elif rules.case_style == NamingRules.CASE_TITLE:
            name = ' '.join(word.capitalize() for word in name.split())
        elif rules.case_style == NamingRules.CASE_SENTENCE:
            name = name.capitalize()
        
        # Replace whitespace with specified separator
        if rules.word_separator == NamingRules.SEPARATOR_UNDERSCORE:
            name = name.replace(' ', '_')
        elif rules.word_separator == NamingRules.SEPARATOR_HYPHEN:
            name = name.replace(' ', '-')
        
        # Remove any remaining special characters
        if rules.remove_special_chars:
            name = re.sub(r'[^\w\s-]', '', name)
        
        # Replace multiple spaces/separators with a single one
        if rules.word_separator == NamingRules.SEPARATOR_SPACE:
            name = re.sub(r'\s+', ' ', name).strip()
        elif rules.word_separator == NamingRules.SEPARATOR_UNDERSCORE:
            name = re.sub(r'_+', '_', name).strip('_')
        elif rules.word_separator == NamingRules.SEPARATOR_HYPHEN:
            name = re.sub(r'-+', '-', name).strip('-')
        
        # Truncate if needed
        if rules.max_length and len(name) > rules.max_length:
            name = name[:rules.max_length].rsplit(' ', 1)[0]
        
        return name
    
    def get_target_path(self, file_path: Path) -> Tuple[Path, str]:
        """Determine the target path for a file based on its category.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (target_directory, new_filename)
        """
        # Default to original name and base directory
        category = None
        rules = self.default_naming
        
        # Find matching category
        for cat in self.categories:
            for pattern in cat.patterns:
                if file_path.match(pattern):
                    category = cat
                    rules = cat.naming_rules
                    break
            if category:
                break
        
        # Get original filename parts
        orig_name = file_path.stem
        extension = file_path.suffix.lower() if rules.preserve_extension else ''
        
        # Normalize the name
        new_name = self.normalize_name(orig_name, rules)
        
        # Add extension if preserving it
        if rules.preserve_extension and extension:
            new_name += extension
        
        # Determine target directory
        if category:
            target_dir = self.base_dir / category.target_dir
        else:
            target_dir = self.base_dir
        
        return target_dir, new_name
    
    def organize_file(self, file_path: Path) -> bool:
        """Organize a single file.
        
        Args:
            file_path: Path to the file to organize
            
        Returns:
            True if successful, False otherwise
        """
        if not file_path.exists() or not file_path.is_file():
            logger.error(f"File does not exist: {file_path}")
            self.stats['errors'] += 1
            return False
        
        self.stats['files_processed'] += 1
        self.stats['processed_size'] += file_path.stat().st_size
        
        # Get target path and new name
        target_dir, new_name = self.get_target_path(file_path)
        target_path = target_dir / new_name
        
        # Skip if no change is needed
        if file_path.parent == target_dir and file_path.name == new_name:
            logger.debug(f"Skipping (no change needed): {file_path}")
            self.stats['files_skipped'] += 1
            return True
        
        # Check if target exists
        if target_path.exists() and not self.overwrite:
            if target_path.samefile(file_path):
                logger.debug(f"Skipping (same file): {file_path}")
                self.stats['files_skipped'] += 1
                return True
            
            # Handle duplicate filenames
            counter = 1
            name_parts = target_path.stem, target_path.suffix
            while target_path.exists():
                new_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                target_path = target_dir / new_name
                counter += 1
        
        # Create target directory if it doesn't exist
        if not target_dir.exists() and not self.dry_run:
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create directory {target_dir}: {e}")
                self.stats['errors'] += 1
                return False
        
        # Move/Rename the file
        try:
            if self.dry_run:
                logger.info(f"Would move: {file_path} -> {target_path}")
            else:
                if file_path.parent != target_path.parent:
                    shutil.move(str(file_path), str(target_path))
                    self.stats['files_moved'] += 1
                    logger.info(f"Moved: {file_path} -> {target_path}")
                else:
                    file_path.rename(target_path)
                    self.stats['files_renamed'] += 1
                    logger.info(f"Renamed: {file_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def organize_directory(self, recursive: bool = True, 
                         pattern: str = '*') -> Dict[str, Any]:
        """Organize files in the base directory.
        
        Args:
            recursive: If True, process subdirectories
            pattern: File pattern to match (e.g., '*.pdf')
            
        Returns:
            Dictionary with operation statistics
        """
        self.stats['start_time'] = datetime.now()
        
        # Process files
        if recursive:
            files = list(self.base_dir.rglob(pattern))
        else:
            files = list(self.base_dir.glob(pattern))
        
        for file_path in files:
            if file_path.is_file():
                self.organize_file(file_path)
        
        # Update statistics
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        self.stats['duration_seconds'] = round(duration, 2)
        
        if self.stats['files_processed'] > 0 and duration > 0:
            self.stats['files_per_second'] = round(
                self.stats['files_processed'] / duration, 2)
            
            processed_mb = self.stats['processed_size'] / (1024 * 1024)
            self.stats['throughput_mb_per_second'] = round(processed_mb / duration, 2)
        
        return self.get_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the operations performed.
        
        Returns:
            Dictionary containing operation statistics
        """
        stats = {
            'files_processed': self.stats['files_processed'],
            'files_moved': self.stats['files_moved'],
            'files_renamed': self.stats['files_renamed'],
            'files_skipped': self.stats['files_skipped'],
            'errors': self.stats['errors'],
            'start_time': self.stats['start_time'].isoformat() if 'start_time' in self.stats else None,
            'end_time': self.stats.get('end_time', datetime.now()).isoformat() if 'end_time' in self.stats else None,
            'processed_size': self.stats.get('processed_size', 0),
            'processed_size_formatted': self._format_size(self.stats.get('processed_size', 0)),
            'dry_run': self.dry_run
        }
        
        if 'duration_seconds' in self.stats:
            stats['duration_seconds'] = self.stats['duration_seconds']
            
            if 'files_per_second' in self.stats:
                stats['files_per_second'] = self.stats['files_per_second']
                
            if 'throughput_mb_per_second' in self.stats:
                stats['throughput_mb_per_second'] = self.stats['throughput_mb_per_second']
        
        return stats
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
