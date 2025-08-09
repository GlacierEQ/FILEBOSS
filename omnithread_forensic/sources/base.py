"""
Base classes and interfaces for data source connectors.
Defines the common interface that all data source connectors must implement.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Type, TypeVar, Union, Any
import logging
from datetime import datetime

from pydantic import BaseModel, HttpUrl, validator

from core.models import (
    Artifact, ArtifactType, ArtifactSource, FileMetadata, 
    ContentMetadata, MediaMetadata, EmailMetadata, EvidenceStatus
)
from config.settings import settings

# Type variable for source configuration models
T = TypeVar('T', bound='BaseSourceConfig')

class SourceConfigError(Exception):
    """Raised when there is an error in source configuration."""
    pass

class SourceConnectionError(Exception):
    """Raised when there is an error connecting to a data source."""
    pass

class SourcePermissionError(Exception):
    """Raised when there are permission issues with a data source."""
    pass

class SourceConfig(BaseModel):
    """Base configuration model for data sources."""
    source_type: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    priority: int = 0  # Higher priority sources are processed first
    
    # Authentication
    auth_method: str  # 'oauth2', 'api_key', 'password', 'none'
    auth_config: Dict[str, Any] = {}
    
    # Connection settings
    base_path: Optional[str] = None
    max_depth: int = 10
    include_recycle_bin: bool = False
    include_hidden: bool = False
    
    # File filtering
    include_patterns: List[str] = []
    exclude_patterns: List[str] = []
    min_file_size: int = 0  # bytes
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Rate limiting
    requests_per_second: float = 5.0
    
    # Metadata
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Source name cannot be empty")
        return v.strip()
    
    @validator('auth_method')
    def validate_auth_method(cls, v):
        valid_methods = ['oauth2', 'api_key', 'password', 'none']
        if v not in valid_methods:
            raise ValueError(f"Invalid auth_method. Must be one of: {', '.join(valid_methods)}")
        return v

class SourceFileInfo(BaseModel):
    """Information about a file in a source system."""
    path: str
    name: str
    size: int
    is_dir: bool = False
    is_file: bool = True
    is_symlink: bool = False
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    accessed: Optional[datetime] = None
    owner: Optional[str] = None
    group: Optional[str] = None
    permissions: Optional[str] = None
    mime_type: Optional[str] = None
    etag: Optional[str] = None  # For change detection
    version: Optional[str] = None  # For versioned files
    extra: Dict[str, Any] = {}
    
    @property
    def extension(self) -> str:
        """Get the file extension in lowercase."""
        return Path(self.name).suffix.lower()
    
    def to_file_metadata(self) -> FileMetadata:
        """Convert to FileMetadata model."""
        return FileMetadata(
            size_bytes=self.size,
            created=self.created,
            modified=self.modified,
            accessed=self.accessed,
            file_type=self.extension,
            mime_type=self.mime_type,
            permissions=self.permissions,
            owner=self.owner,
            group=self.group,
        )

class BaseSource(ABC):
    """
    Abstract base class for all data source connectors.
    
    Subclasses must implement all abstract methods to provide
    access to the underlying data source.
    """
    
    def __init__(self, config: SourceConfig):
        """Initialize the data source with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{config.name}]")
        self.connected = False
        self.stats = {
            'files_processed': 0,
            'bytes_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
        }
    
    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Type[SourceConfig]:
        """Return the configuration model for this source type."""
        raise NotImplementedError
    
    @classmethod
    def create(cls, config: Dict) -> 'BaseSource':
        """Create a new source instance from a configuration dictionary."""
        config_model = cls.get_config_schema()
        config_obj = config_model(**config)
        return cls(config_obj)
    
    async def connect(self) -> None:
        """Establish connection to the data source."""
        if self.connected:
            return
            
        self.stats['start_time'] = datetime.utcnow()
        self.logger.info(f"Connecting to {self.config.name}...")
        
        try:
            await self._connect()
            self.connected = True
            self.logger.info(f"Successfully connected to {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.config.name}: {str(e)}")
            self.connected = False
            raise SourceConnectionError(f"Failed to connect to {self.config.name}: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close connection to the data source."""
        if not self.connected:
            return
            
        try:
            await self._disconnect()
            self.stats['end_time'] = datetime.utcnow()
            self.logger.info(f"Disconnected from {self.config.name}")
        except Exception as e:
            self.logger.error(f"Error disconnecting from {self.config.name}: {str(e)}")
            raise
        finally:
            self.connected = False
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()
    
    @abstractmethod
    async def _connect(self) -> None:
        """Internal method to establish connection."""
        raise NotImplementedError
    
    @abstractmethod
    async def _disconnect(self) -> None:
        """Internal method to close connection."""
        raise NotImplementedError
    
    @abstractmethod
    async def list_files(
        self, 
        path: Optional[str] = None, 
        recursive: bool = False,
        include_metadata: bool = False
    ) -> List[SourceFileInfo]:
        """
        List files in the specified path.
        
        Args:
            path: Path to list files from. If None, list from root.
            recursive: If True, list files recursively.
            include_metadata: If True, include file metadata.
            
        Returns:
            List of file information objects.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def get_file(
        self, 
        path: str,
        download: bool = False
    ) -> Optional[Union[bytes, 'SourceFileInfo']]:
        """
        Get file content or metadata.
        
        Args:
            path: Path to the file.
            download: If True, download file content. If False, return metadata only.
            
        Returns:
            File content as bytes if download=True, otherwise SourceFileInfo.
            Returns None if file not found.
        """
        raise NotImplementedError
    
    async def get_artifact_source(self, file_info: SourceFileInfo) -> ArtifactSource:
        """
        Create an ArtifactSource from file information.
        
        Args:
            file_info: Source file information.
            
        Returns:
            ArtifactSource instance.
        """
        return ArtifactSource(
            source_type=self.config.source_type,
            source_id=file_info.etag or file_info.path,
            path=file_info.path,
            original_name=file_info.name,
            source_created=file_info.created,
            source_modified=file_info.modified,
            source_metadata={
                'size': file_info.size,
                'mime_type': file_info.mime_type,
                'owner': file_info.owner,
                'permissions': file_info.permissions,
                **file_info.extra
            }
        )
    
    async def to_artifact(self, file_info: SourceFileInfo) -> Optional[Artifact]:
        """
        Convert a source file to an Artifact.
        
        Args:
            file_info: Source file information.
            
        Returns:
            Artifact instance or None if the file should be skipped.
        """
        # Skip directories
        if file_info.is_dir:
            return None
            
        # Apply filters
        if not self._should_process_file(file_info):
            self.logger.debug(f"Skipping file (filters): {file_info.path}")
            return None
            
        # Create artifact source
        source = await self.get_artifact_source(file_info)
        
        # Determine artifact type
        artifact_type = self._get_artifact_type(file_info)
        
        # Create base artifact
        artifact = Artifact(
            artifact_type=artifact_type,
            name=file_info.name,
            file_metadata=file_info.to_file_metadata(),
        )
        artifact.add_source(source)
        
        # Update stats
        self.stats['files_processed'] += 1
        self.stats['bytes_processed'] += file_info.size
        
        return artifact
    
    def _get_artifact_type(self, file_info: SourceFileInfo) -> ArtifactType:
        """Determine the artifact type from file information."""
        # Default to file extension mapping
        ext = file_info.extension.lower()
        
        # Document types
        if ext in ['.pdf', '.docx', '.doc', '.odt', '.rtf', '.txt', '.md']:
            return ArtifactType.DOCUMENT
            
        # Image types
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            return ArtifactType.IMAGE
            
        # Audio types
        if ext in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
            return ArtifactType.AUDIO
            
        # Video types
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            return ArtifactType.VIDEO
            
        # Email types
        if ext in ['.eml', '.msg']:
            return ArtifactType.EMAIL
            
        # Archive types
        if ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return ArtifactType.ARCHIVE
            
        return ArtifactType.OTHER
    
    def _should_process_file(self, file_info: SourceFileInfo) -> bool:
        """
        Determine if a file should be processed based on configuration.
        
        Args:
            file_info: Source file information.
            
        Returns:
            True if the file should be processed, False otherwise.
        """
        # Skip directories
        if file_info.is_dir:
            return False
            
        # Skip hidden files if configured
        if not self.config.include_hidden and file_info.name.startswith('.'):
            return False
            
        # Check file size limits
        if file_info.size < self.config.min_file_size:
            return False
            if file_info.size > self.config.max_file_size:
                return False
                
        # Check include/exclude patterns
        path_str = str(Path(file_info.path).as_posix())
        
        # If include patterns are specified, file must match at least one
        if self.config.include_patterns:
            if not any(Path(path_str).match(p) for p in self.config.include_patterns):
                return False
                
        # File must not match any exclude patterns
        if any(Path(path_str).match(p) for p in self.config.exclude_patterns):
            return False
            
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        duration = None
        if self.stats['start_time']:
            end = self.stats['end_time'] or datetime.utcnow()
            duration = (end - self.stats['start_time']).total_seconds()
            
        return {
            **self.stats,
            'duration_seconds': duration,
            'bytes_per_second': (
                self.stats['bytes_processed'] / duration 
                if duration and duration > 0 else 0
            ),
            'files_per_second': (
                self.stats['files_processed'] / duration 
                if duration and duration > 0 else 0
            ),
        }
