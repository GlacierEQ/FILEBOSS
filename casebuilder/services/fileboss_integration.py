"""
FileBoss Integration Service

This module provides integration between the CaseBuilder system and the FileBoss/FileSystemMaster
functionality, allowing for unified file processing, organization, and analysis.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import shutil
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class FileType(Enum):
    """Supported file types for processing."""
    DOCUMENT = auto()
    IMAGE = auto()
    AUDIO = auto()
    VIDEO = auto()
    ARCHIVE = auto()
    CODE = auto()
    DATA = auto()
    OTHER = auto()

@dataclass
class FileMetadata:
    """Metadata for files being processed."""
    path: Path
    name: str
    size: int
    file_type: FileType
    extension: str
    mime_type: str
    created: float
    modified: float
    hash: str = ""
    case_id: Optional[str] = None
    evidence_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class FileBossIntegrator:
    """
    Integrates FileBoss/FileSystemMaster functionality with CaseBuilder.
    
    This class provides methods to process, organize, and analyze files while
    maintaining integration with the CaseBuilder system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the FileBoss integrator.
        
        Args:
            config: Configuration dictionary for the integrator
        """
        self.config = config or {}
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize FileSystemMaster components."""
        try:
            # Import FileSystemMaster components
            from PROJECT_HEAD.FileSystemMaster.FileSystemMaster.file_processor import FileProcessor
            from PROJECT_HEAD.FileSystemMaster.FileSystemMaster.file_organizer import FileOrganizer
            from PROJECT_HEAD.FileSystemMaster.FileSystemMaster.config import Config
            
            # Initialize configuration
            self.fs_config = Config()
            
            # Initialize components
            self.file_processor = FileProcessor(self.fs_config)
            self.file_organizer = FileOrganizer(self.fs_config)
            
            # Set up supported extensions mapping
            self.supported_extensions = {
                'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.md', '.odt'],
                'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
                'audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
                'video': ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm'],
                'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
                'code': ['.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.rb', '.php', '.swift'],
                'data': ['.json', '.xml', '.csv', '.xls', '.xlsx', '.db', '.sqlite']
            }
            
        except ImportError as e:
            logger.error(f"Failed to initialize FileSystemMaster components: {e}")
            raise
    
    async def process_directory(
        self,
        directory: Union[str, Path],
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[FileMetadata]:
        """Process all files in a directory and return metadata.
        
        Args:
            directory: Directory to process
            case_id: Optional case ID to associate with files
            evidence_id: Optional evidence ID to associate with files
            recursive: Whether to process subdirectories
            file_types: List of file types to include (e.g., ['document', 'image'])
            
        Returns:
            List of FileMetadata objects for processed files
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")
        
        # Get list of files to process
        files = self._scan_directory(directory, recursive, file_types)
        
        # Process files
        processed_files = []
        for file_info in files:
            try:
                # Enhance with additional metadata
                metadata = await self._enhance_metadata(file_info)
                metadata.case_id = case_id
                metadata.evidence_id = evidence_id
                
                # Process with FileSystemMaster
                processed_data = self.file_processor.process_file(file_info['path'])
                metadata.metadata.update(processed_data)
                
                processed_files.append(metadata)
                
            except Exception as e:
                logger.error(f"Error processing file {file_info['path']}: {e}")
                continue
        
        return processed_files
    
    async def organize_files(
        self,
        files: List[Union[FileMetadata, Dict]],
        output_dir: Union[str, Path],
        organization_scheme: str = "type_date"
    ) -> List[Dict[str, str]]:
        """Organize files according to the specified scheme.
        
        Args:
            files: List of files to organize (FileMetadata objects or dictionaries)
            output_dir: Base directory for organized files
            organization_scheme: Scheme to use for organization
                - 'type_date': Organize by file type and date
                - 'type': Organize by file type only
                - 'date': Organize by date only
                - 'flat': All files in a single directory
                
        Returns:
            List of dictionaries with original and new file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for file_info in files:
            try:
                if isinstance(file_info, FileMetadata):
                    src_path = file_info.path
                    file_type = file_info.file_type.name.lower()
                    modified_date = datetime.fromtimestamp(file_info.modified).strftime('%Y-%m-%d')
                else:
                    src_path = Path(file_info.get('path', ''))
                    file_type = file_info.get('type', 'other').lower()
                    modified_date = datetime.fromtimestamp(
                        file_info.get('modified', 0)
                    ).strftime('%Y-%m-%d')
                
                # Determine destination path based on organization scheme
                if organization_scheme == 'type_date':
                    dest_dir = output_dir / file_type / modified_date
                elif organization_scheme == 'type':
                    dest_dir = output_dir / file_type
                elif organization_scheme == 'date':
                    dest_dir = output_dir / modified_date
                else:  # 'flat'
                    dest_dir = output_dir
                
                # Create destination directory if it doesn't exist
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file to new location
                dest_path = dest_dir / src_path.name
                shutil.copy2(src_path, dest_path)
                
                results.append({
                    'original_path': str(src_path),
                    'new_path': str(dest_path),
                    'file_type': file_type,
                    'organization_scheme': organization_scheme
                })
                
            except Exception as e:
                logger.error(f"Error organizing file {file_info.get('path', 'unknown')}: {e}")
                continue
        
        return results
    
    async def link_to_case(self, file_path: Union[str, Path], case_id: str) -> bool:
        """Link a file to a specific case.
        
        Args:
            file_path: Path to the file
            case_id: ID of the case to link to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
                
            # In a real implementation, this would update the database or metadata store
            # For now, we'll just log the action
            logger.info(f"Linked file {file_path} to case {case_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error linking file to case: {e}")
            return False
    
    async def link_to_evidence(self, file_path: Union[str, Path], evidence_id: str) -> bool:
        """Link a file to a specific evidence item.
        
        Args:
            file_path: Path to the file
            evidence_id: ID of the evidence to link to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
                
            # In a real implementation, this would update the database or metadata store
            # For now, we'll just log the action
            logger.info(f"Linked file {file_path} to evidence {evidence_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error linking file to evidence: {e}")
            return False
    
    def _scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Scan a directory for files of the specified types.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            file_types: List of file types to include (e.g., ['document', 'image'])
            
        Returns:
            List of file information dictionaries
        """
        files = []
        
        # If no file types specified, include all supported types
        if not file_types:
            file_types = list(self.supported_extensions.keys())
        
        # Get all extensions for the specified file types
        extensions = []
        for ft in file_types:
            if ft in self.supported_extensions:
                extensions.extend(self.supported_extensions[ft])
        
        # Convert to set for faster lookups
        extensions = set(extensions)
        
        # Scan directory
        glob_pattern = '**/*' if recursive else '*'
        for file_path in directory.glob(glob_pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                try:
                    stat = file_path.stat()
                    files.append({
                        'path': file_path,
                        'name': file_path.name,
                        'extension': file_path.suffix.lower(),
                        'size': stat.st_size,
                        'created': stat.st_ctime,
                        'modified': stat.st_mtime,
                        'type': self._get_file_type(file_path.suffix.lower())
                    })
                except OSError as e:
                    logger.warning(f"Could not access file {file_path}: {e}")
                    continue
        
        return files
    
    async def _enhance_metadata(self, file_info: Dict) -> FileMetadata:
        """Enhance file metadata with additional information.
        
        Args:
            file_info: Basic file information dictionary
            
        Returns:
            Enhanced FileMetadata object
        """
        file_path = Path(file_info['path'])
        
        # Get MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Create FileMetadata object
        metadata = FileMetadata(
            path=file_path,
            name=file_info['name'],
            size=file_info['size'],
            file_type=file_info['type'],
            extension=file_info['extension'],
            mime_type=mime_type or 'application/octet-stream',
            created=file_info['created'],
            modified=file_info['modified'],
            metadata=file_info  # Include original file info
        )
        
        return metadata
    
    def _get_file_type(self, extension: str) -> FileType:
        """Determine the file type from the extension.
        
        Args:
            extension: File extension (with leading dot)
            
        Returns:
            FileType enum value
        """
        extension = extension.lower()
        
        for file_type, extensions in self.supported_extensions.items():
            if extension in extensions:
                return FileType[file_type.upper()]
        
        return FileType.OTHER

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize integrator
        integrator = FileBossIntegrator()
        
        # Process a directory
        try:
            files = await integrator.process_directory(
                "/path/to/files",
                case_id="case123",
                file_types=["document", "image"]
            )
            
            print(f"Processed {len(files)} files")
            
            # Organize files
            results = await integrator.organize_files(
                files,
                "/path/to/output",
                organization_scheme="type_date"
            )
            
            print(f"Organized {len(results)} files")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(main())
