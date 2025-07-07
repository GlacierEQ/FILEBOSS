from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from ..db.models import TimelineEventType


class TimelineEventBase(BaseModel):
    case_id: UUID
    title: str
    event_type: TimelineEventType
    description: Optional[str] = None


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[TimelineEventType] = None
