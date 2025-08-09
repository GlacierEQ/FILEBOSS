"""
File Organizer Service

This module provides intelligent file organization and renaming functionality
for the CaseBuilder system, automatically sorting files into hierarchical
case folders based on metadata and content analysis.
"""

import os
import re
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from datetime import datetime
import hashlib
import mimetypes
from dataclasses import dataclass, field
from enum import Enum, auto

from ..config import settings
from .metadata_extractors import extract_metadata, extract_text_content

# Configure logging
logger = logging.getLogger(__name__)

class FileCategory(Enum):
    """Categories for different types of files."""
    EVIDENCE = "Evidence"
    DOCUMENT = "Documents"
    MEDIA = "Media"
    EMAIL = "Email"
    DATABASE = "Databases"
    LOGS = "Logs"
    ARCHIVE = "Archives"
    OTHER = "Other"

@dataclass
class FileMetadata:
    """Metadata for files being processed."""
    path: Path
    name: str
    size: int
    extension: str
    mime_type: str
    created: float
    modified: float
    category: FileCategory = FileCategory.OTHER
    case_id: Optional[str] = None
    subcase_id: Optional[str] = None
    document_date: Optional[datetime] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def file_hash(self) -> str:
        """Generate a hash of the file contents."""
        hasher = hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

class FileOrganizer:
    """
    Handles intelligent file organization and renaming for case files.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the file organizer with optional base path."""
        self.base_path = Path(base_path) if base_path else settings.storage.base_path
        self.temp_path = settings.storage.temp_path
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
    
    def organize_file(self, file_path: Union[str, Path], 
                     case_id: str, 
                     subcase_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Organize a single file into the appropriate case directory.
        
        Args:
            file_path: Path to the file to organize
            case_id: The case identifier
            subcase_id: Optional subcase identifier
            metadata: Additional file metadata
            
        Returns:
            Path: The new path of the organized file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract file metadata
        file_meta = self._extract_metadata(file_path, case_id, subcase_id, metadata)
        
        # Determine target directory structure
        target_dir = self._get_target_directory(file_meta)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate new filename
        new_filename = self._generate_filename(file_meta)
        target_path = target_dir / new_filename
        
        # Handle file conflicts
        if target_path.exists():
            if self._files_identical(file_path, target_path):
                logger.info(f"Duplicate file detected, skipping: {file_path}")
                return target_path
            target_path = self._handle_duplicate(target_path)
        
        # Move/copy the file
        try:
            shutil.move(str(file_path), str(target_path))
            logger.info(f"Moved {file_path} to {target_path}")
        except Exception as e:
            logger.error(f"Error moving file {file_path}: {e}")
            raise
            
        return target_path
    
    def _extract_metadata(self, file_path: Path, 
                         case_id: str, 
                         subcase_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> FileMetadata:
        """Extract metadata from a file."""
        if metadata is None:
            metadata = {}
            
        # Get basic file stats
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Create file metadata
        file_meta = FileMetadata(
            path=file_path,
            name=file_path.name,
            size=stat.st_size,
            extension=file_path.suffix.lower(),
            mime_type=mime_type or 'application/octet-stream',
            created=stat.st_ctime,
            modified=stat.st_mtime,
            case_id=case_id,
            subcase_id=subcase_id,
            tags=metadata.get('tags', []),
            metadata=metadata
        )
        
        # Categorize file
        file_meta.category = self._categorize_file(file_meta)
        
        # Extract additional metadata based on file type
        self._extract_additional_metadata(file_meta)
        
        return file_meta
    
    def _categorize_file(self, file_meta: FileMetadata) -> FileCategory:
        """Categorize the file based on its extension and MIME type."""
        # Document types
        doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', 
                         '.xls', '.xlsx', '.ods', '.csv', '.ppt', '.pptx', '.odp'}
        
        # Media types
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif'}
        video_extensions = {'.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg'}
        audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma', '.aiff'}
        
        # Special types
        email_extensions = {'.msg', '.eml', '.pst', '.ost', '.mbox'}
        db_extensions = {'.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.db3'}
        
        ext = file_meta.extension.lower()
        
        # First try to determine from MIME type if available
        mime_type = file_meta.mime_type.lower()
        
        if any(doc_type in mime_type for doc_type in ['pdf', 'document', 'msword', 'excel', 'powerpoint', 'text']):
            return FileCategory.DOCUMENT
        elif any(img_type in mime_type for img_type in ['image']):
            return FileCategory.MEDIA
        elif any(vid_type in mime_type for vid_type in ['video']):
            return FileCategory.MEDIA
        elif any(aud_type in mime_type for aud_type in ['audio']):
            return FileCategory.MEDIA
        elif any(mail_type in mime_type for mail_type in ['message', 'rfc822']):
            return FileCategory.EMAIL
            
        # Fall back to extension-based categorization
        if ext in doc_extensions:
            return FileCategory.DOCUMENT
        elif ext in image_extensions:
            return FileCategory.MEDIA
        elif ext in video_extensions:
            return FileCategory.MEDIA
        elif ext in audio_extensions:
            return FileCategory.MEDIA
        elif ext in email_extensions:
            return FileCategory.EMAIL
        elif ext in db_extensions:
            return FileCategory.DATABASE
        elif ext in {'.log', '.txt'} and 'log' in file_meta.name.lower():
            return FileCategory.LOGS
        elif ext in {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.zst'}:
            return FileCategory.ARCHIVE
        else:
            # Try to extract content to determine type
            try:
                text = extract_text_content(file_meta.path)
                if len(text) > 100:  # If we found substantial text
                    return FileCategory.DOCUMENT
            except Exception as e:
                logger.debug(f"Could not extract text for categorization: {e}")
                
            return FileCategory.OTHER
    
    def _extract_additional_metadata(self, file_meta: FileMetadata) -> None:
        """Extract additional metadata based on file type."""
        try:
            # Extract metadata using the metadata extractors
            metadata = extract_metadata(file_meta.path)
            
            # Update file metadata with extracted data
            if 'title' in metadata:
                file_meta.description = metadata['title']
                
            # Handle document dates
            for date_field in ['created', 'modified', 'date_taken', 'parsed_date']:
                if date_field in metadata:
                    try:
                        if isinstance(metadata[date_field], str):
                            # Parse string dates
                            from dateutil.parser import parse
                            file_meta.document_date = parse(metadata[date_field])
                        elif isinstance(metadata[date_field], datetime):
                            file_meta.document_date = metadata[date_field]
                        break
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Could not parse date {date_field}: {e}")
            
            # Add extracted text as a tag for searchability
            if 'extracted_text' in metadata and metadata['extracted_text']:
                file_meta.tags.append('has_text_content')
                
            # Store all extracted metadata
            file_meta.metadata.update(metadata)
            
            logger.debug(f"Extracted metadata for {file_meta.path}: {metadata}")
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_meta.path}: {e}")
            logger.debug(f"Metadata extraction error details:", exc_info=True)
    
    def _get_target_directory(self, file_meta: FileMetadata) -> Path:
        """Determine the target directory for a file based on its metadata."""
        # Base case directory
        path_parts = [self.base_path, file_meta.case_id]
        
        # Add subcase if available
        if file_meta.subcase_id:
            path_parts.append(file_meta.subcase_id)
        
        # Add file category
        path_parts.append(file_meta.category.value)
        
        # Additional subdirectories based on file type or date
        if file_meta.document_date:
            # Organize by year/month
            path_parts.extend([
                str(file_meta.document_date.year),
                f"{file_meta.document_date.month:02d}"
            ])
        
        return Path(*path_parts)
    
    def _generate_filename(self, file_meta: FileMetadata) -> str:
        """Generate a standardized filename based on metadata."""
        parts = []
        
        # Add case and subcase identifiers
        parts.append(file_meta.case_id)
        if file_meta.subcase_id:
            parts.append(file_meta.subcase_id)
        
        # Add date if available (prefer document date, then creation date)
        date_to_use = None
        if file_meta.document_date:
            date_to_use = file_meta.document_date
        elif 'created' in file_meta.metadata:
            try:
                from dateutil.parser import parse
                date_to_use = parse(str(file_meta.metadata['created']))
            except (ValueError, TypeError):
                pass
                
        if date_to_use:
            parts.append(date_to_use.strftime("%Y%m%d"))
        
        # Add description or original name
        if file_meta.description:
            # Clean and normalize the description
            clean_desc = re.sub(r'[^\w\-\.]', '_', file_meta.description)
            clean_desc = re.sub(r'_+', '_', clean_desc).strip('_')
            # Limit length to avoid path too long errors
            clean_desc = clean_desc[:100]
            if clean_desc:
                parts.append(clean_desc)
        
        # If we still don't have enough parts, use the original name (sanitized)
        if len(parts) < 3:  # case_id + [subcase_id] + [date] = at least 2-3 parts
            orig_name = file_meta.path.stem
            # Clean the original name
            clean_name = re.sub(r'[^\w\-\.]', '_', orig_name)
            clean_name = re.sub(r'_+', '_', clean_name).strip('_')
            if clean_name and clean_name not in parts:  # Avoid duplication
                parts.append(clean_name)
        
        # Ensure we have at least some identifier
        if len(parts) == 1:  # Only case_id
            parts.append('document')
        
        # Add extension (always use lowercase for consistency)
        ext = file_meta.extension.lower()
        
        # Join parts with double underscore for better readability
        filename = f"{'__'.join(parts)}{ext}"
        
        # Ensure filename is not too long (max 255 chars including extension)
        max_length = 255 - len(ext)
        if len(filename) > max_length:
            # Keep the end with extension, truncate from the start
            filename = f"...{filename[-(max_length-3):]}{ext}"
        
        return filename
    
    def _files_identical(self, file1: Path, file2: Path) -> bool:
        """Check if two files are identical by comparing hashes."""
        if file1.stat().st_size != file2.stat().st_size:
            return False
            
        hash1 = self._calculate_file_hash(file1)
        hash2 = self._calculate_file_hash(file2)
        return hash1 == hash2
    
    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _handle_duplicate(self, target_path: Path) -> Path:
        """Handle duplicate filenames by appending a counter."""
        counter = 1
        parent = target_path.parent
        stem = target_path.stem
        ext = target_path.suffix
        
        while target_path.exists():
            target_path = parent / f"{stem}_{counter}{ext}"
            counter += 1
            
        return target_path
    
    def organize_directory(self, source_dir: Union[str, Path], 
                         case_id: str,
                         subcase_id: Optional[str] = None,
                         recursive: bool = True) -> List[Path]:
        """
        Organize all files in a directory.
        
        Args:
            source_dir: Directory containing files to organize
            case_id: The case identifier
            subcase_id: Optional subcase identifier
            recursive: Whether to process subdirectories
            
        Returns:
            List of Path objects for the organized files
        """
        source_dir = Path(source_dir)
        if not source_dir.is_dir():
            raise NotADirectoryError(f"Source is not a directory: {source_dir}")
        
        organized_files = []
        
        # Process files in the directory
        for item in source_dir.iterdir():
            if item.is_file():
                try:
                    target_path = self.organize_file(
                        item, case_id, subcase_id)
                    organized_files.append(target_path)
                except Exception as e:
                    logger.error(f"Error organizing file {item}: {e}")
            elif recursive and item.is_dir():
                # Recursively process subdirectories
                organized_files.extend(
                    self.organize_directory(item, case_id, subcase_id, recursive)
                )
        
        return organized_files

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <source_path> <case_id> [subcase_id]")
        sys.exit(1)
    
    source_path = Path(sys.argv[1])
    case_id = sys.argv[2]
    subcase_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    organizer = FileOrganizer()
    
    if source_path.is_file():
        try:
            result = organizer.organize_file(source_path, case_id, subcase_id)
            print(f"Organized file: {result}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif source_path.is_dir():
        try:
            results = organizer.organize_directory(source_path, case_id, subcase_id)
            print(f"Organized {len(results)} files")
            for result in results:
                print(f"- {result}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: {source_path} does not exist", file=sys.stderr)
        sys.exit(1)
