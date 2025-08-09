"""Directory model for organizing files and subdirectories."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File


class Directory(Base):
    """Directory model for organizing files and subdirectories."""
    
    __tablename__ = "directories"
    
    # Directory identification
    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Name of the directory",
    )
    
    # Directory metadata
    path = Column(
        String(1024),
        nullable=False,
        index=True,
        doc="Relative path of the directory from the storage root",
    )
    
    # Directory relationships
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("directories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    parent: Mapped[Optional["Directory"]] = relationship(
        "Directory",
        remote_side="Directory.id",
        back_populates="subdirectories",
    )
    
    subdirectories: Mapped[List["Directory"]] = relationship(
        "Directory",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    files: Mapped[List["File"]] = relationship(
        "File",
        back_populates="directory",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="directories",
    )
    
    # Directory status
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the directory and its contents are publicly accessible",
    )
    
    is_trashed = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the directory is in the trash",
    )
    
    trashed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the directory was moved to trash",
    )
    
    # Directory statistics
    file_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of files in this directory (not including subdirectories)",
    )
    
    total_file_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of files in this directory and all subdirectories",
    )
    
    total_size = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total size of all files in this directory and subdirectories in bytes",
    )
    
    # Timestamps
    last_accessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the directory was last accessed",
    )
    
    last_modified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=datetime.utcnow,
        doc="When the directory was last modified",
    )
    
    # Methods
    def __str__(self) -> str:
        """String representation of the directory."""
        return self.path
    
    @property
    def full_path(self) -> Path:
        """Get the full filesystem path to the directory."""
        return Path(settings.UPLOAD_FOLDER) / self.path.lstrip("/")
    
    @property
    def url(self) -> str:
        """Get the URL to access the directory."""
        return f"{settings.SERVER_HOST}/api/v1/directories/{self.id}"
    
    def update_last_accessed(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()
        if self.parent:
            self.parent.update_last_accessed()
    
    def move_to_trash(self) -> None:
        """Move the directory to trash."""
        self.is_trashed = True
        self.trashed_at = datetime.utcnow()
        
        # Recursively mark all subdirectories and files as trashed
        for subdir in self.subdirectories:
            subdir.move_to_trash()
        
        for file in self.files:
            file.move_to_trash()
    
    def restore_from_trash(self) -> None:
        """Restore the directory from trash."""
        self.is_trashed = False
        self.trashed_at = None
        
        # Recursively restore all subdirectories and files
        for subdir in self.subdirectories:
            subdir.restore_from_trash()
        
        for file in self.files:
            file.restore_from_trash()
    
    def get_metadata(self) -> dict:
        """Get directory metadata as a dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "path": self.path,
            "is_public": self.is_public,
            "is_trashed": self.is_trashed,
            "file_count": self.file_count,
            "total_file_count": self.total_file_count,
            "total_size": self.total_size,
            "owner_id": str(self.owner_id),
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "last_modified_at": self.last_modified_at.isoformat() if self.last_modified_at else None,
            "url": self.url,
        }
    
    def update_statistics(self) -> None:
        """Update directory statistics (file count, size, etc.)."""
        # Update direct file count and size
        self.file_count = len(self.files)
        direct_size = sum(file.size for file in self.files)
        
        # Update subdirectory statistics
        subdir_file_count = 0
        subdir_size = 0
        
        for subdir in self.subdirectories:
            subdir.update_statistics()
            subdir_file_count += subdir.total_file_count
            subdir_size += subdir.total_size
        
        # Update total counts
        self.total_file_count = self.file_count + subdir_file_count
        self.total_size = direct_size + subdir_size
        
        # Update parent directory if exists
        if self.parent:
            self.parent.update_statistics()
    
    @classmethod
    def create_root_directory(cls, owner_id: UUID, name: str = "Root") -> 'Directory':
        """Create a root directory for a user."""
        return cls(
            name=name,
            path="",
            owner_id=owner_id,
            is_public=False,
            is_trashed=False,
        )
    
    def create_subdirectory(self, name: str, owner_id: Optional[UUID] = None) -> 'Directory':
        """Create a subdirectory within this directory."""
        # Clean the directory name
        name = name.strip().replace('/', '_').replace('\\', '_')
        
        # Create the subdirectory
        subdir = Directory(
            name=name,
            path=f"{self.path}/{name}" if self.path else name,
            owner_id=owner_id or self.owner_id,
            parent=self,
            is_public=self.is_public,
            is_trashed=self.is_trashed,
        )
        
        # Add to subdirectories
        self.subdirectories.append(subdir)
        
        # Update statistics
        self.update_statistics()
        
        return subdir
