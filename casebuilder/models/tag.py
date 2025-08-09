"""
Tag Models

This module contains the SQLAlchemy models for tags and their relationships.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Table, Index
from sqlalchemy.orm import relationship

from .base import Base

# Association table for many-to-many relationship between files and tags
file_tags = Table(
    'file_tags',
    Base.metadata,
    Column('file_id', String(64), ForeignKey('files.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', String(64), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('value', Text, nullable=True),  # Optional value for the tag
    Column('created_by', String(128), nullable=True),
    Index('idx_file_tags_file_id', 'file_id'),
    Index('idx_file_tags_tag_id', 'tag_id'),
    Index('idx_file_tags_composite', 'file_id', 'tag_id', unique=True)
)

class Tag(Base):
    """Model representing a tag that can be applied to files."""
    
    __tablename__ = "tags"
    
    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(32), nullable=True)  # For UI display
    created_by = Column(String(128), nullable=True)
    
    # Relationships
    files = relationship(
        "File",
        secondary=file_tags,
        back_populates="tags",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Tag(id='{self.id}', name='{self.name}')>"


class FileTag(Base):
    """Association model for files and tags with additional attributes."""
    
    __tablename__ = "file_tags"
    __table_args__ = {'extend_existing': True}  # Allow extending the existing table
    
    file_id = Column(String(64), ForeignKey('files.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(String(64), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
    value = Column(Text, nullable=True)  # Optional value for the tag
    created_by = Column(String(128), nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="file_tags")
    tag = relationship("Tag", back_populates="file_tags")
    
    def __repr__(self):
        return f"<FileTag(file_id='{self.file_id}', tag_id='{self.tag_id}')>"

# Update the backref from File to FileTag
from .file import File
File.file_tags = relationship("FileTag", back_populates="file")
