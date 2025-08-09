"""
Tag Schemas

This module contains Pydantic models for tag-related operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, validator

from .base import BaseModel, BaseResponse

class TagBase(BaseModel):
    """Base schema for tag operations."""
    name: str = Field(..., max_length=128, description="Name of the tag")
    description: Optional[str] = Field(None, description="Description of the tag")
    color: Optional[str] = Field(None, description="Color code for the tag (e.g., '#FF0000')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the tag")
    
    @validator('color')
    def validate_color(cls, v):
        """Validate color format (if provided)."""
        if v is not None:
            if not v.startswith('#'):
                v = '#' + v
            if len(v) not in [4, 7]:  # #RGB or #RRGGBB
                raise ValueError("Color must be in #RGB or #RRGGBB format")
            # Validate hex characters
            if not all(c in '0123456789ABCDEFabcdef' for c in v[1:]):
                raise ValueError("Color must be a valid hex color code")
        return v

class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass

class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""
    name: Optional[str] = Field(None, max_length=128, description="Updated name of the tag")
    description: Optional[str] = Field(None, description="Updated description of the tag")
    color: Optional[str] = Field(None, description="Updated color code for the tag")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata for the tag")
    
    @validator('color')
    def validate_color(cls, v):
        """Validate color format (if provided)."""
        if v is not None:
            if not v.startswith('#'):
                v = '#' + v
            if len(v) not in [4, 7]:  # #RGB or #RRGGBB
                raise ValueError("Color must be in #RGB or #RRGGBB format")
            # Validate hex characters
            if not all(c in '0123456789ABCDEFabcdef' for c in v[1:]):
                raise ValueError("Color must be a valid hex color code")
        return v

class TagInDB(TagBase):
    """Schema for tag data as stored in the database."""
    id: str = Field(..., description="Unique identifier for the tag")
    created_at: datetime = Field(..., description="When the tag was created")
    updated_at: datetime = Field(..., description="When the tag was last updated")
    created_by: Optional[str] = Field(None, description="User who created the tag")
    
    class Config:
        orm_mode = True

class TagResponse(BaseResponse[TagInDB]):
    """Response schema for a single tag."""
    data: Optional[TagInDB] = None

class TagListResponse(BaseResponse):
    """Response schema for a list of tags with pagination."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing tags and pagination info"
    )
    
    @classmethod
    def from_queryset(
        cls, 
        tags: list, 
        total: int, 
        page: int, 
        size: int
    ) -> 'TagListResponse':
        """Create a paginated response from a queryset."""
        pages = (total + size - 1) // size if size > 0 else 1
        return cls(
            success=True,
            data={
                "items": tags,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }
        )

# File-Tag Association Schemas
class FileTagBase(BaseModel):
    """Base schema for file-tag association operations."""
    value: Optional[str] = Field(None, description="Optional value for the tag association")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the association")

class FileTagCreate(FileTagBase):
    """Schema for creating a new file-tag association."""
    file_id: str = Field(..., description="ID of the file")
    tag_name: str = Field(..., description="Name of the tag")
    created_by: Optional[str] = Field(None, description="User who created the association")

class FileTagUpdate(FileTagBase):
    """Schema for updating a file-tag association."""
    value: Optional[str] = Field(None, description="Updated value for the tag association")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata for the association")

class FileTagInDB(FileTagBase):
    """Schema for file-tag association data as stored in the database."""
    file_id: str = Field(..., description="ID of the file")
    tag_id: str = Field(..., description="ID of the tag")
    created_at: datetime = Field(..., description="When the association was created")
    created_by: Optional[str] = Field(None, description="User who created the association")
    
    class Config:
        orm_mode = True

class FileTagResponse(BaseResponse[FileTagInDB]):
    """Response schema for a single file-tag association."""
    data: Optional[FileTagInDB] = None

class FileTagListResponse(BaseResponse):
    """Response schema for a list of file-tag associations with pagination."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing file-tag associations and pagination info"
    )
    
    @classmethod
    def from_queryset(
        cls, 
        file_tags: list, 
        total: int, 
        page: int, 
        size: int
    ) -> 'FileTagListResponse':
        """Create a paginated response from a queryset."""
        pages = (total + size - 1) // size if size > 0 else 1
        return cls(
            success=True,
            data={
                "items": file_tags,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }
        )

# Tag Usage Statistics
class TagUsageStats(BaseModel):
    """Schema for tag usage statistics."""
    tag_id: str = Field(..., description="ID of the tag")
    tag_name: str = Field(..., description="Name of the tag")
    usage_count: int = Field(..., ge=0, description="Number of times the tag is used")
    last_used: Optional[datetime] = Field(None, description="When the tag was last used")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TagStatsResponse(BaseResponse):
    """Response schema for tag statistics."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing tag statistics"
    )
    
    @classmethod
    def from_stats(
        cls, 
        stats: List[TagUsageStats],
        total_tags: int,
        total_usage: int
    ) -> 'TagStatsResponse':
        """Create a response from tag statistics."""
        return cls(
            success=True,
            data={
                "stats": stats,
                "total_tags": total_tags,
                "total_usage": total_usage
            }
        )

# Tag Search and Filtering
class TagSearchRequest(BaseModel):
    """Schema for tag search requests."""
    query: Optional[str] = Field(None, description="Search query string")
    min_usage: Optional[int] = Field(None, ge=0, description="Minimum number of times the tag is used")
    max_usage: Optional[int] = Field(None, ge=0, description="Maximum number of times the tag is used")
    sort_by: Optional[str] = Field("name", description="Field to sort by (name, usage, last_used)")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc or desc)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        valid_fields = ['name', 'usage', 'last_used', 'created_at']
        if v.lower() not in valid_fields:
            raise ValueError(f"sort_by must be one of {', '.join(valid_fields)}")
        return v.lower()
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort_order field."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower()
