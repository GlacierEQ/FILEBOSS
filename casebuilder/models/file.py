"""
File and Metadata Models

This module contains the SQLAlchemy models for files and their metadata.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Integer, Boolean, LargeBinary, 
    Float, JSON, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum

from .base import Base

class FileCategory(str, PyEnum):
    """Categories for file types."""
    EVIDENCE = "Evidence"
    DOCUMENT = "Documents"
    MEDIA = "Media"
    EMAIL = "Email"
    DATABASE = "Databases"
    LOGS = "Logs"
    ARCHIVE = "Archives"
    OTHER = "Other"

class File(Base):
    """Model representing a file in the system."""
    
    __tablename__ = "files"
    
    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    subcase_id = Column(String(64), ForeignKey("subcases.id", ondelete="SET NULL"), nullable=True)
    
    # File information
    original_name = Column(String(512), nullable=False)
    stored_path = Column(String(1024), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    mime_type = Column(String(256), nullable=True)
    file_extension = Column(String(32), nullable=True)
    
    # Categorization
    category = Column(Enum(FileCategory), default=FileCategory.OTHER)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    file_created = Column(DateTime(timezone=True), nullable=True)
    file_modified = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="files")
    subcase = relationship("Subcase", back_populates="files")
    metadata = relationship("FileMetadata", back_populates="file", uselist=False)
    versions = relationship("FileVersion", back_populates="file")
    tags = relationship("FileTag", back_populates="file")
    
    def __repr__(self):
        return f"<File(id='{self.id}', original_name='{self.original_name}')>"


class FileMetadata(Base):
    """Extended metadata for files."""
    
    __tablename__ = "file_metadata"
    
    file_id = Column(String(64), ForeignKey("files.id", ondelete="CASCADE"), primary_key=True)
    
    # Document metadata
    title = Column(String(512), nullable=True)
    author = Column(String(256), nullable=True)
    subject = Column(String(512), nullable=True)
    keywords = Column(JSON, nullable=True)  # List of keywords
    description = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Media metadata
    width = Column(Integer, nullable=True)  # For images/videos
    height = Column(Integer, nullable=True)  # For images/videos
    duration = Column(Float, nullable=True)  # For audio/video in seconds
    
    # Technical metadata
    software = Column(String(256), nullable=True)
    encoding = Column(String(128), nullable=True)
    
    # Extracted text content (or path to external storage)
    extracted_text = Column(Text, nullable=True)
    
    # Raw metadata as JSON for flexible storage
    raw_metadata = Column(JSON, nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="metadata")
    
    def __repr__(self):
        return f"<FileMetadata(file_id='{self.file_id}')>"


class FileVersion(Base):
    """Model for tracking file versions."""
    
    __tablename__ = "file_versions"
    
    id = Column(String(64), primary_key=True, index=True)
    file_id = Column(String(64), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    
    # Version information
    version_number = Column(Integer, nullable=False)
    changes = Column(Text, nullable=True)
    
    # File information
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(128), nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="versions")
    
    # Ensure unique version numbers per file
    __table_args__ = (
        UniqueConstraint('file_id', 'version_number', name='uq_file_version'),
        Index('idx_file_version', 'file_id', 'version_number')
    )
    
    def __repr__(self):
        return f"<FileVersion(id='{self.id}', file_id='{self.file_id}', version={self.version_number})>"
