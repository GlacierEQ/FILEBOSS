from typing import Optional, List
from pydantic import BaseModel

from ..db.models import EvidenceType, EvidenceStatus


class EvidenceBase(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = None
    evidence_type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.PENDING_REVIEW
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    tags: Optional[List[str]] = None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[EvidenceStatus] = None
    tags: Optional[List[str]] = None
