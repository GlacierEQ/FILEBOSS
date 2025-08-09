""
Base Schemas

This module contains the base Pydantic models used throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel as PydanticBaseModel
from pydantic.generics import GenericModel
from pydantic import Field, validator

# Type variable for generic response models
T = TypeVar('T')

class BaseModel(PydanticBaseModel):
    """Base model with common configuration."""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        orm_mode = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

class BaseResponse(GenericModel, Generic[T]):
    """Base response model with success flag and optional data."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    
    @classmethod
    def success_response(
        cls, 
        data: Any = None, 
        message: Optional[str] = None
    ) -> 'BaseResponse':
        """Create a success response."""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(
        cls, 
        message: str, 
        data: Any = None
    ) -> 'BaseResponse':
        """Create an error response."""
        return cls(success=False, message=message, data=data)

class PaginatedResponse(GenericModel, Generic[T]):
    """Paginated response model."""
    items: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 10
    pages: int = 1
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
