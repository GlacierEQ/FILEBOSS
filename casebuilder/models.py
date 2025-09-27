"""Convenience exports for ORM models and API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .db.models import (
    Base,
    Evidence as OrmEvidence,
    EvidenceStatus,
    EvidenceType,
    TimelineEvent as OrmTimelineEvent,
    TimelineEventType,
)

# Re-export ORM models for external consumers
Evidence = OrmEvidence
TimelineEvent = OrmTimelineEvent


class EvidenceBase(BaseModel):
    """Shared attributes for evidence API schemas."""

    title: str = Field(..., description="Human readable evidence title")
    description: Optional[str] = Field(None, description="Evidence description")
    case_id: str = Field(..., description="Associated case identifier")
    evidence_type: EvidenceType = Field(
        default=EvidenceType.DOCUMENT,
        description="Classification of evidence",
    )
    status: EvidenceStatus = Field(
        default=EvidenceStatus.PENDING_REVIEW,
        description="Workflow status for the evidence",
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Path to the evidence file on disk",
    )
    file_type: Optional[str] = Field(
        default=None,
        description="Detected MIME type for the evidence file",
    )
    file_size: Optional[int] = Field(
        default=None,
        description="Size of the evidence file in bytes",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags applied to the evidence",
    )


class EvidenceCreate(EvidenceBase):
    """Schema used when creating evidence records through the API."""

    pass


class EvidenceUpdate(BaseModel):
    """Schema used when updating evidence records."""

    title: Optional[str] = Field(None, description="Updated evidence title")
    description: Optional[str] = Field(None, description="Updated description")
    status: Optional[EvidenceStatus] = Field(None, description="Updated workflow status")
    tags: Optional[List[str]] = Field(None, description="Updated evidence tags")


class EvidenceRead(EvidenceBase):
    """Schema returned when reading evidence records from the API."""

    id: str = Field(..., description="Primary identifier for the evidence")
    created_at: datetime = Field(..., description="Timestamp when the evidence was created")

    class Config:
        """Pydantic configuration for ORM compatibility."""

        from_attributes = True


class TimelineEventBase(BaseModel):
    """Shared attributes for timeline event schemas."""

    title: str = Field(..., description="Timeline event title")
    description: Optional[str] = Field(None, description="Event description")
    event_type: TimelineEventType = Field(
        default=TimelineEventType.OTHER, description="Event classification"
    )
    event_date: datetime = Field(..., description="Primary timestamp for the event")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional event metadata"
    )


class TimelineEventCreate(TimelineEventBase):
    """Schema used when creating timeline events."""

    case_id: str = Field(..., description="Associated case identifier")
    created_by_id: str = Field(..., description="User responsible for the event")


class TimelineEventUpdate(BaseModel):
    """Schema used when updating timeline events."""

    title: Optional[str] = Field(None, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")
    event_type: Optional[TimelineEventType] = Field(None, description="Updated event type")
    event_date: Optional[datetime] = Field(None, description="Updated event date")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata payload")


__all__ = [
    "Base",
    "Evidence",
    "EvidenceCreate",
    "EvidenceUpdate",
    "EvidenceRead",
    "EvidenceStatus",
    "EvidenceType",
    "TimelineEvent",
    "TimelineEventType",
    "TimelineEventCreate",
    "TimelineEventUpdate",
]
