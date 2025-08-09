"""
File Schemas

This module contains Pydantic models for file-related operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import Field, validator, HttpUrl

from .base import BaseModel, BaseResponse

class FileCategory(str, Enum):
    """Categories for file types."""
    EVIDENCE = "Evidence"
    DOCUMENT = "Documents"
    MEDIA = "Media"
    EMAIL = "Email"
    DATABASE = "Databases"
    LOGS = "Logs"
    ARCHIVE = "Archives"
    OTHER = "Other"

class FileBase(BaseModel):
    """Base schema for file operations."""
    original_name: str = Field(..., description="Original name of the file")
    stored_path: str = Field(..., description="Path where the file is stored")
    file_size: int = Field(..., ge=0, description="Size of the file in bytes")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of the file content")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    file_extension: Optional[str] = Field(None, description="File extension without the dot")
    category: FileCategory = Field(FileCategory.OTHER, description="Category of the file")
    case_id: str = Field(..., description="ID of the associated case")
    subcase_id: Optional[str] = Field(None, description="ID of the associated subcase, if any")
    file_created: Optional[datetime] = Field(None, description="Creation timestamp of the original file")
    file_modified: Optional[datetime] = Field(None, description="Last modification timestamp of the original file")
    tags: Optional[List[str]] = Field(None, description="List of tags associated with the file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the file")

class FileCreate(FileBase):
    """Schema for creating a new file record."""
    pass

class FileUpdate(BaseModel):
    """Schema for updating an existing file record."""
    original_name: Optional[str] = Field(None, description="Updated original name of the file")
    mime_type: Optional[str] = Field(None, description="Updated MIME type of the file")
    category: Optional[FileCategory] = Field(None, description="Updated category of the file")
    subcase_id: Optional[str] = Field(None, description="Updated associated subcase ID")
    tags: Optional[List[str]] = Field(None, description="Updated list of tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata for the file")

class FileInDB(FileBase):
    """Schema for file data as stored in the database."""
    id: str = Field(..., description="Unique identifier for the file")
    created_at: datetime = Field(..., description="When the file record was created")
    updated_at: datetime = Field(..., description="When the file record was last updated")
    
    class Config:
        orm_mode = True

class FileResponse(BaseResponse[FileInDB]):
    """Response schema for a single file."""
    data: Optional[FileInDB] = None

class FileListResponse(BaseResponse):
    """Response schema for a list of files with pagination."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing files and pagination info"
    )

# File Metadata Schemas
class FileMetadataBase(BaseModel):
    """Base schema for file metadata operations."""
    title: Optional[str] = Field(None, max_length=512, description="Title extracted from the file")
    author: Optional[str] = Field(None, max_length=256, description="Author of the file")
    subject: Optional[str] = Field(None, max_length=512, description="Subject of the file")
    keywords: Optional[List[str]] = Field(None, description="Keywords extracted from the file")
    description: Optional[str] = Field(None, description="Description of the file")
    page_count: Optional[int] = Field(None, ge=0, description="Number of pages in the document")
    width: Optional[int] = Field(None, ge=0, description="Width in pixels (for images/videos)")
    height: Optional[int] = Field(None, ge=0, description="Height in pixels (for images/videos)")
    duration: Optional[float] = Field(None, ge=0, description="Duration in seconds (for audio/video)")
    software: Optional[str] = Field(None, description="Software used to create the file")
    encoding: Optional[str] = Field(None, description="Character encoding of the file")
    extracted_text: Optional[str] = Field(None, description="Text extracted from the file")
    raw_metadata: Optional[Dict[str, Any]] = Field(None, description="Raw metadata extracted from the file")

class FileMetadataCreate(FileMetadataBase):
    """Schema for creating file metadata."""
    pass

class FileMetadataUpdate(FileMetadataBase):
    """Schema for updating file metadata."""
    pass

class FileMetadataInDB(FileMetadataBase):
    """Schema for file metadata as stored in the database."""
    file_id: str = Field(..., description="ID of the associated file")
    
    class Config:
        orm_mode = True

class FileMetadataResponse(BaseResponse[FileMetadataInDB]):
    """Response schema for file metadata."""
    data: Optional[FileMetadataInDB] = None

# File Version Schemas
class FileVersionBase(BaseModel):
    """Base schema for file version operations."""
    version_number: int = Field(..., ge=1, description="Version number")
    file_path: str = Field(..., description="Path to the versioned file")
    file_size: int = Field(..., ge=0, description="Size of the versioned file in bytes")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of the versioned file")
    changes: Optional[str] = Field(None, description="Description of changes in this version")
    created_by: Optional[str] = Field(None, description="User who created this version")

class FileVersionCreate(FileVersionBase):
    """Schema for creating a new file version."""
    file_id: str = Field(..., description="ID of the parent file")

class FileVersionInDB(FileVersionBase):
    """Schema for file version data as stored in the database."""
    id: str = Field(..., description="Unique identifier for the file version")
    file_id: str = Field(..., description="ID of the parent file")
    created_at: datetime = Field(..., description="When the version was created")
    
    class Config:
        orm_mode = True

class FileVersionResponse(BaseResponse[FileVersionInDB]):
    """Response schema for a single file version."""
    data: Optional[FileVersionInDB] = None

class FileVersionListResponse(BaseResponse):
    """Response schema for a list of file versions with pagination."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing file versions and pagination info"
    )

# Combined Response Schemas
class FileWithMetadataResponse(FileResponse):
    """Response schema for a file with its metadata."""
    metadata: Optional[FileMetadataInDB] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# File Upload Schemas
class FileUploadRequest(BaseModel):
    """Schema for file upload requests."""
    case_id: str = Field(..., description="ID of the case to associate the file with")
    subcase_id: Optional[str] = Field(None, description="ID of the subcase to associate the file with")
    category: Optional[FileCategory] = Field(FileCategory.OTHER, description="Category for the file")
    tags: Optional[List[str]] = Field(None, description="Tags to associate with the file")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the file")

class FileUploadResponse(FileResponse):
    """Response schema for file uploads."""
    presigned_url: Optional[HttpUrl] = Field(None, description="URL for direct upload to storage")
    upload_id: Optional[str] = Field(None, description="ID for tracking multi-part uploads")

# File Search Schemas
class FileSearchRequest(BaseModel):
    """Schema for file search requests."""
    query: Optional[str] = Field(None, description="Search query string")
    case_id: Optional[str] = Field(None, description="Filter by case ID")
    subcase_id: Optional[str] = Field(None, description="Filter by subcase ID")
    category: Optional[FileCategory] = Field(None, description="Filter by file category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    mime_type: Optional[str] = Field(None, description="Filter by MIME type")
    min_size: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    date_from: Optional[datetime] = Field(None, description="Filter by creation date (from)")
    date_to: Optional[datetime] = Field(None, description="Filter by creation date (to)")
    sort_by: Optional[str] = Field("created_at", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc or desc)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower()

# File Export Schemas
class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    PDF = "pdf"

class FileExportRequest(FileSearchRequest):
    """Schema for file export requests."""
    format: ExportFormat = Field(ExportFormat.CSV, description="Export format")
    include_metadata: bool = Field(True, description="Whether to include file metadata in the export")
    include_content: bool = Field(False, description="Whether to include file content in the export")
    
class FileExportResponse(BaseResponse):
    """Response schema for file exports."""
    download_url: Optional[HttpUrl] = Field(None, description="URL to download the exported file")
    expires_at: Optional[datetime] = Field(None, description="When the download URL expires")
