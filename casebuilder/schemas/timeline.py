from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..db.models import TimelineEventType
from ..utils import utc_now


class TimelineEventBase(BaseModel):
    case_id: UUID
    event_type: TimelineEventType
    title: str
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[TimelineEventType] = None
    metadata: Optional[Dict[str, Any]] = None
