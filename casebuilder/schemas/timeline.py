from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from ..db.models import TimelineEventType

class TimelineEventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: TimelineEventType
    event_date: datetime
    end_date: Optional[datetime] = None
    is_important: bool = False
    metadata_: Optional[Dict[str, Any]] = None

class TimelineEventCreate(TimelineEventBase):
    case_id: UUID
    created_by_id: UUID
    evidence_id: Optional[UUID] = None

class TimelineEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[TimelineEventType] = None
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_important: Optional[bool] = None
    metadata_: Optional[Dict[str, Any]] = None

class TimelineEventInDBBase(TimelineEventBase):
    id: UUID
    case_id: UUID
    created_by_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class TimelineEvent(TimelineEventInDBBase):
    pass

class TimelineEventInDB(TimelineEventInDBBase):
    pass
