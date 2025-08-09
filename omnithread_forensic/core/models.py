"""
Core data models for the Omnithread Forensic Protocol.
Defines the data structures for forensic artifacts, metadata, and relationships.
"""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, validator, AnyUrl

from config.settings import settings

# Enums for consistent types
class ArtifactType(str, Enum):
    """Types of forensic artifacts."""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    EMAIL = "email"
    MESSAGE = "message"
    DATABASE = "database"
    LOG = "log"
    OTHER = "other"

class EvidenceStatus(str, Enum):
    """Status of evidence processing and verification."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    DELETED = "deleted"

class RelationshipType(str, Enum):
    """Types of relationships between artifacts."""
    DERIVED_FROM = "derived_from"
    CONTAINS = "contains"
    RELATED_TO = "related_to"
    VERSION_OF = "version_of"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    MENTIONS = "mentions"

class HashAlgorithm(str, Enum):
    """Supported hashing algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"

# Base Models
class HashValue(BaseModel):
    """Represents a hash value with its algorithm."""
    algorithm: HashAlgorithm
    value: str
    
    def __str__(self) -> str:
        return f"{self.algorithm}:{self.value}"

class FileMetadata(BaseModel):
    """File system metadata for an artifact."""
    size_bytes: int = 0
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    accessed: Optional[datetime] = None
    file_type: Optional[str] = None
    mime_type: Optional[str] = None
    permissions: Optional[str] = None
    owner: Optional[str] = None
    group: Optional[str] = None
    inode: Optional[int] = None
    device: Optional[int] = None
    nlink: Optional[int] = None
    uid: Optional[int] = None
    gid: Optional[int] = None
    
class ContentMetadata(BaseModel):
    """Content-specific metadata extracted from files."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = []
    language: Optional[str] = "en"
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    has_embedded_files: bool = False
    is_encrypted: bool = False
    is_password_protected: bool = False
    
class MediaMetadata(BaseModel):
    """Metadata specific to media files (images, audio, video)."""
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    frame_rate: Optional[float] = None
    bit_rate: Optional[int] = None
    codec: Optional[str] = None
    color_space: Optional[str] = None
    dpi: Optional[float] = None
    has_audio: bool = False
    has_video: bool = False
    
class EmailMetadata(BaseModel):
    """Metadata specific to email messages."""
    message_id: Optional[str] = None
    subject: Optional[str] = None
    from_: Optional[str] = Field(None, alias="from")
    to: List[str] = []
    cc: List[str] = []
    bcc: List[str] = []
    date: Optional[datetime] = None
    in_reply_to: Optional[str] = None
    references: List[str] = []
    
class ArtifactSource(BaseModel):
    """Source information for an artifact."""
    source_type: str  # e.g., "local_fs", "google_drive", "dropbox", "email"
    source_id: str  # Unique identifier in the source system
    path: str  # Path/URL in the source system
    original_name: Optional[str] = None
    source_created: Optional[datetime] = None
    source_modified: Optional[datetime] = None
    source_metadata: Dict[str, Any] = {}
    
class ArtifactRelationship(BaseModel):
    """Represents a relationship between two artifacts."""
    source_id: UUID
    target_id: UUID
    relationship_type: RelationshipType
    confidence: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = {}
    created: datetime = Field(default_factory=datetime.utcnow)
    
class ArtifactProcessingLog(BaseModel):
    """Log entry for artifact processing."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str  # "info", "warning", "error"
    message: str
    details: Optional[Dict[str, Any]] = None
    
class Artifact(BaseModel):
    """Core artifact model representing any digital evidence item."""
    id: UUID = Field(default_factory=uuid4)
    artifact_type: ArtifactType
    name: str
    description: Optional[str] = None
    
    # Content and hashes
    content: Optional[bytes] = None
    content_text: Optional[str] = None
    content_encoding: Optional[str] = None
    hashes: Dict[HashAlgorithm, str] = {}
    
    # Source information
    sources: List[ArtifactSource] = []
    
    # Metadata
    file_metadata: Optional[FileMetadata] = None
    content_metadata: Optional[ContentMetadata] = None
    media_metadata: Optional[MediaMetadata] = None
    email_metadata: Optional[EmailMetadata] = None
    custom_metadata: Dict[str, Any] = {}
    
    # Processing status
    status: EvidenceStatus = EvidenceStatus.PENDING
    processing_errors: List[str] = []
    processing_logs: List[ArtifactProcessingLog] = []
    
    # Relationships
    parent_id: Optional[UUID] = None
    related_artifact_ids: Set[UUID] = set()
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Indexing and search
    tags: Set[str] = set()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Path: str,
            set: list,  # Convert sets to lists for JSON serialization
        }
    
    def add_source(self, source: ArtifactSource) -> None:
        """Add a source to this artifact."""
        self.sources.append(source)
        self.updated_at = datetime.utcnow()
    
    def add_relationship(
        self, 
        target_id: UUID, 
        relationship_type: RelationshipType,
        **metadata
    ) -> ArtifactRelationship:
        """Create a relationship to another artifact."""
        relationship = ArtifactRelationship(
            source_id=self.id,
            target_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {}
        )
        self.related_artifact_ids.add(target_id)
        self.updated_at = datetime.utcnow()
        return relationship
    
    def add_processing_log(
        self, 
        message: str, 
        level: str = "info", 
        **details
    ) -> None:
        """Add a processing log entry."""
        log = ArtifactProcessingLog(
            level=level,
            message=message,
            details=details or None
        )
        self.processing_logs.append(log)
        self.updated_at = datetime.utcnow()
    
    def update_status(self, status: EvidenceStatus) -> None:
        """Update the processing status of this artifact."""
        self.status = status
        if status == EvidenceStatus.COMPLETED:
            self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

# Specialized artifact models for type safety
class DocumentArtifact(Artifact):
    """Specialized artifact for document files."""
    artifact_type: ArtifactType = ArtifactType.DOCUMENT
    content_metadata: Optional[ContentMetadata] = Field(
        default_factory=ContentMetadata
    )

class ImageArtifact(Artifact):
    """Specialized artifact for image files."""
    artifact_type: ArtifactType = ArtifactType.IMAGE
    media_metadata: MediaMetadata = Field(default_factory=MediaMetadata)

class AudioArtifact(Artifact):
    """Specialized artifact for audio files."""
    artifact_type: ArtifactType = ArtifactType.AUDIO
    media_metadata: MediaMetadata = Field(default_factory=MediaMetadata)

class VideoArtifact(Artifact):
    """Specialized artifact for video files."""
    artifact_type: ArtifactType = ArtifactType.VIDEO
    media_metadata: MediaMetadata = Field(default_factory=MediaMetadata)

class EmailArtifact(Artifact):
    """Specialized artifact for email messages."""
    artifact_type: ArtifactType = ArtifactType.EMAIL
    email_metadata: EmailMetadata = Field(default_factory=EmailMetadata)
    
    class Config:
        allow_population_by_field_name = True  # Allow "from" as field name

# Type aliases for better type hints
ArtifactT = Union[
    Artifact,
    DocumentArtifact,
    ImageArtifact,
    AudioArtifact,
    VideoArtifact,
    EmailArtifact
]
