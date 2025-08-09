"""
Pydantic Schemas

This module contains all the Pydantic models used for request/response validation
and serialization in the CaseBuilder API.
"""

from .base import BaseModel, BaseResponse
from .case import CaseCreate, CaseUpdate, CaseInDB, CaseResponse
from .file import (
    FileCreate, FileUpdate, FileInDB, FileResponse,
    FileMetadataCreate, FileMetadataUpdate, FileMetadataResponse,
    FileVersionCreate, FileVersionResponse, FileWithMetadataResponse
)
from .tag import TagCreate, TagUpdate, TagInDB, TagResponse, FileTagCreate, FileTagResponse

__all__ = [
    # Base
    'BaseModel', 'BaseResponse',
    
    # Case
    'CaseCreate', 'CaseUpdate', 'CaseInDB', 'CaseResponse',
    
    # File
    'FileCreate', 'FileUpdate', 'FileInDB', 'FileResponse',
    'FileMetadataCreate', 'FileMetadataUpdate', 'FileMetadataResponse',
    'FileVersionCreate', 'FileVersionResponse', 'FileWithMetadataResponse',
    
    # Tag
    'TagCreate', 'TagUpdate', 'TagInDB', 'TagResponse',
    'FileTagCreate', 'FileTagResponse'
]
