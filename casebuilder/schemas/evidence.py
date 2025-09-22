from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..db.models import EvidenceType, EvidenceStatus


class EvidenceBase(BaseModel):
    title: str
    description: Optional[str] = None
    evidence_type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.PENDING_REVIEW
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    case_id: UUID
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[EvidenceStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class EvidenceInDB(EvidenceBase):
    id: UUID
    exhibit_number: Optional[str] = None
    chain_of_custody: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
