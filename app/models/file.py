"""File model for storing file metadata and content."""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.directory import Directory


class FileType(str, Enum):
    """Supported file types."""
    FILE = "file"
    IMAGE = "image"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    OTHER = "other"


class File(Base):
    """File model for storing file metadata and content."""
    
    __tablename__ = "files"
    
    # File identification
    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Name of the file including extension",
    )
    
    # File metadata
    path = Column(
        String(1024),
        nullable=False,
        index=True,
        doc="Relative path of the file from the storage root",
    )
    
    file_type = Column(
        String(50),
        nullable=False,
        default=FileType.FILE,
        doc="Type of the file (e.g., image, document, etc.)",
    )
    
    mime_type = Column(
        String(255),
        nullable=True,
        doc="MIME type of the file",
    )
    
    size = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Size of the file in bytes",
    )
    
    extension = Column(
        String(50),
        nullable=True,
        doc="File extension without the dot",
    )
    
    # File content and storage
    storage_path = Column(
        String(1024),
        nullable=True,
        doc="Internal storage path (if different from the public path)",
    )
    
    is_encrypted = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the file content is encrypted",
    )
    
    # File status
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the file is publicly accessible",
    )
    
    is_trashed = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the file is in the trash",
    )
    
    trashed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the file was moved to trash",
    )
    
    # Versioning
    version = Column(
        Integer,
        default=1,
        nullable=False,
        doc="Current version of the file",
    )
    
    # Relationships
    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="files",
    )
    
    directory_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("directories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    directory: Mapped[Optional["Directory"]] = relationship(
        "Directory",
        back_populates="files",
    )
    
    # Timestamps
    last_accessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the file was last accessed",
    )
    
    last_modified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow,
        doc="When the file was last modified",
    )
    
    # Methods
    def __str__(self) -> str:
        """String representation of the file."""
        return self.name
    
    @property
    def full_path(self) -> Path:
        """Get the full filesystem path to the file."""
        return Path(settings.UPLOAD_FOLDER) / self.path.lstrip("/")
    
    @property
    def url(self) -> str:
        """Get the URL to access the file."""
        return f"{settings.SERVER_HOST}/api/v1/files/{self.id}/download"
    
    @property
    def thumbnail_url(self) -> Optional[str]:
        """Get the URL to the file's thumbnail (if available)."""
        if self.file_type in (FileType.IMAGE, FileType.VIDEO):
            return f"{settings.SERVER_HOST}/api/v1/files/{self.id}/thumbnail"
        return None
    
    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()
    
    def move_to_trash(self) -> None:
        """Move the file to trash."""
        self.is_trashed = True
        self.trashed_at = datetime.utcnow()
    
    def restore_from_trash(self) -> None:
        """Restore the file from trash."""
        self.is_trashed = False
        self.trashed_at = None
    
    def get_metadata(self) -> dict:
        """Get file metadata as a dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "path": self.path,
            "type": self.file_type,
            "mime_type": self.mime_type,
            "size": self.size,
            "extension": self.extension,
            "is_public": self.is_public,
            "is_trashed": self.is_trashed,
            "version": self.version,
            "owner_id": str(self.owner_id),
            "directory_id": str(self.directory_id) if self.directory_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "last_modified_at": self.last_modified_at.isoformat() if self.last_modified_at else None,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
        }
    
    @classmethod
    def get_file_type(cls, filename: str) -> str:
        """Determine the file type based on the file extension."""
        if not filename:
            return FileType.OTHER
        
        ext = os.path.splitext(filename)[1].lower()
        
        # Image extensions
        image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
            '.ico', '.heic', '.heif', '.raw', '.cr2', '.nef', '.dng'
        }
        
        # Document extensions
        document_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.odt', '.ods', '.odp', '.txt', '.rtf', '.md', '.csv', '.tsv',
            '.pages', '.numbers', '.key', '.epub', '.mobi', '.azw', '.azw3'
        }
        
        # Archive extensions
        archive_extensions = {
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.z',
            '.iso', '.dmg', '.pkg', '.deb', '.rpm', '.msi'
        }
        
        # Audio extensions
        audio_extensions = {
            '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a',
            '.aiff', '.alac', '.opus', '.midi', '.mid'
        }
        
        # Video extensions
        video_extensions = {
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
            '.m4v', '.mpg', '.mpeg', '.3gp', '.m2ts', '.mts', '.vob'
        }
        
        # Code extensions
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h',
            '.hpp', '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.dart',
            '.rs', '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd', '.sql',
            '.html', '.css', '.scss', '.sass', '.less', '.json', '.xml',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env',
            '.dockerfile', '.dockerignore', '.gitignore', '.gitattributes',
            '.md', '.markdown', '.rst', '.tex', '.log'
        }
        
        if ext in image_extensions:
            return FileType.IMAGE
        elif ext in document_extensions:
            return FileType.DOCUMENT
        elif ext in archive_extensions:
            return FileType.ARCHIVE
        elif ext in audio_extensions:
            return FileType.AUDIO
        elif ext in video_extensions:
            return FileType.VIDEO
        elif ext in code_extensions:
            return FileType.CODE
        else:
            return FileType.OTHER
