from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..db.models import CaseStatus


class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: CaseStatus = CaseStatus.DRAFT
    case_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    court_name: Optional[str] = None
    owner_id: UUID


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CaseStatus] = None
    case_number: Optional[str] = None
    jurisdiction: Optional[str] = None
    court_name: Optional[str] = None
