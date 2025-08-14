from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from ..db.models import EvidenceType, EvidenceStatus

class EvidenceBase(BaseModel):
    title: str
    description: Optional[str] = None
    evidence_type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.PENDING_REVIEW
    exhibit_number: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None

class EvidenceCreate(EvidenceBase):
    case_id: UUID
    document_id: Optional[UUID] = None

class EvidenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[EvidenceStatus] = None
    exhibit_number: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None

class EvidenceInDBBase(EvidenceBase):
    id: UUID
    case_id: UUID
    document_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Evidence(EvidenceInDBBase):
    pass

class EvidenceInDB(EvidenceInDBBase):
    pass
