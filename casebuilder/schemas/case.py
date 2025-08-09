""
Case Schemas

This module contains the Pydantic models for case-related operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, validator
from .base import BaseModel, BaseResponse

class CaseBase(BaseModel):
    """Base schema for case operations."""
    title: str = Field(..., max_length=256, description="Title of the case")
    description: Optional[str] = Field(None, description="Detailed description of the case")
    status: str = Field("open", description="Current status of the case")
    assigned_to: Optional[str] = Field(None, description="User ID of the assignee")
    tags: Optional[List[str]] = Field(None, description="List of tags for the case")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the case"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status field."""
        valid_statuses = ["open", "in_progress", "closed", "archived"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of {', '.join(valid_statuses)}")
        return v.lower()

class CaseCreate(CaseBase):
    """Schema for creating a new case."""
    pass

class CaseUpdate(BaseModel):
    """Schema for updating an existing case."""
    title: Optional[str] = Field(None, max_length=256, description="Updated title of the case")
    description: Optional[str] = Field(None, description="Updated description of the case")
    status: Optional[str] = Field(None, description="Updated status of the case")
    assigned_to: Optional[str] = Field(None, description="Updated assignee user ID")
    tags: Optional[List[str]] = Field(None, description="Updated list of tags")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Updated metadata for the case"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status field if provided."""
        if v is not None:
            valid_statuses = ["open", "in_progress", "closed", "archived"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"Status must be one of {', '.join(valid_statuses)}")
            return v.lower()
        return v

class CaseInDB(CaseBase):
    """Schema for case data as stored in the database."""
    id: str = Field(..., description="Unique identifier for the case")
    created_at: datetime = Field(..., description="When the case was created")
    updated_at: datetime = Field(..., description="When the case was last updated")
    created_by: str = Field(..., description="User ID of the case creator")
    
    class Config:
        orm_mode = True

class CaseResponse(BaseResponse[CaseInDB]):
    """Response schema for a single case."""
    data: Optional[CaseInDB] = None

class CaseListResponse(BaseResponse):
    """Response schema for a list of cases with pagination."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing cases and pagination info"
    )
    
    @classmethod
    def from_queryset(
        cls, 
        cases: list, 
        total: int, 
        page: int, 
        size: int
    ) -> 'CaseListResponse':
        """Create a paginated response from a queryset."""
        pages = (total + size - 1) // size if size > 0 else 1
        return cls(
            success=True,
            data={
                "items": cases,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }
        )

# Subcase schemas
class SubcaseBase(BaseModel):
    """Base schema for subcase operations."""
    title: str = Field(..., max_length=256, description="Title of the subcase")
    description: Optional[str] = Field(None, description="Detailed description of the subcase")
    status: str = Field("open", description="Current status of the subcase")
    case_id: str = Field(..., description="ID of the parent case")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the subcase"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status field."""
        valid_statuses = ["open", "in_progress", "on_hold", "closed"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of {', '.join(valid_statuses)}")
        return v.lower()

class SubcaseCreate(SubcaseBase):
    """Schema for creating a new subcase."""
    pass

class SubcaseUpdate(BaseModel):
    """Schema for updating an existing subcase."""
    title: Optional[str] = Field(None, max_length=256, description="Updated title of the subcase")
    description: Optional[str] = Field(None, description="Updated description of the subcase")
    status: Optional[str] = Field(None, description="Updated status of the subcase")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Updated metadata for the subcase"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status field if provided."""
        if v is not None:
            valid_statuses = ["open", "in_progress", "on_hold", "closed"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"Status must be one of {', '.join(valid_statuses)}")
            return v.lower()
        return v

class SubcaseInDB(SubcaseBase):
    """Schema for subcase data as stored in the database."""
    id: str = Field(..., description="Unique identifier for the subcase")
    created_at: datetime = Field(..., description="When the subcase was created")
    updated_at: datetime = Field(..., description="When the subcase was last updated")
    
    class Config:
        orm_mode = True

class SubcaseResponse(BaseResponse[SubcaseInDB]):
    """Response schema for a single subcase."""
    data: Optional[SubcaseInDB] = None

class SubcaseListResponse(BaseResponse):
    """Response schema for a list of subcases with pagination."""
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object containing subcases and pagination info"
    )
    
    @classmethod
    def from_queryset(
        cls, 
        subcases: list, 
        total: int, 
        page: int, 
        size: int
    ) -> 'SubcaseListResponse':
        """Create a paginated response from a queryset."""
        pages = (total + size - 1) // size if size > 0 else 1
        return cls(
            success=True,
            data={
                "items": subcases,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages
            }
        )
