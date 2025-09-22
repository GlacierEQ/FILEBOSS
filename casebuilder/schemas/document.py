from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..db.models import DocumentType, DocumentStatus


class DocumentBase(BaseModel):
    case_id: UUID
    title: str
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    document_type: DocumentType = DocumentType.OTHER
    status: DocumentStatus = DocumentStatus.DRAFT
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DocumentStatus] = None
    metadata: Optional[Dict[str, Any]] = None
