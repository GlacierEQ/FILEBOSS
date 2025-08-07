"""
Database models for Mega CaseBuilder 3000.
"""
import uuid
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Table,
    Type,
    TypeVar,
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

# Using String for UUID storage in SQLite
from sqlalchemy import String as UUIDString

if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped, mapped_column

# Type variables for generic return types
T = TypeVar('T')

from .base import Base

# Association tables
case_participants = Table(
    "case_participants",
    Base.metadata,
    Column("case_id", UUIDString(36), ForeignKey("cases.id"), primary_key=True),
    Column("user_id", UUIDString(36), ForeignKey("users.id"), primary_key=True),
    Column("role", String(50), nullable=False, default="collaborator"),
)

case_tags = Table(
    "case_tags",
    Base.metadata,
    Column("case_id", UUIDString(36), ForeignKey("cases.id"), primary_key=True),
    Column("tag_id", UUIDString(36), ForeignKey("tags.id"), primary_key=True),
)


document_relationships = Table(
    "document_relationships",
    Base.metadata,
    Column(
        "parent_document_id", 
        String(36), 
        ForeignKey("documents.id"), 
        primary_key=True
    ),
    Column(
        "child_document_id", 
        String(36), 
        ForeignKey("documents.id"), 
        primary_key=True
    ),
    Column("relationship_type", String(50), nullable=False, default="related"),
)


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(UUIDString(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    cases = relationship("Case", back_populates="owner")
    documents = relationship("Document", back_populates="uploaded_by")
    events = relationship("TimelineEvent", back_populates="created_by")
    participant_in = relationship(
        "Case", 
        secondary=case_participants, 
        back_populates="participants"
    )

    @validates("email")
    def validate_email(self, key: str, email: str) -> str:
        """Validate email format."""
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email.lower()

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class CaseStatus(str, Enum):
    """Case status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Case(Base):
    """Case model representing a legal case."""

    __tablename__ = "cases"

    id = Column(UUIDString(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(CaseStatus), default=CaseStatus.DRAFT)
    case_number = Column(String(100), unique=True, nullable=True)
    jurisdiction = Column(String(100), nullable=True)
    court_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Foreign keys
    owner_id = Column(UUIDString(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="cases")
    participants = relationship(
        "User", 
        secondary=case_participants, 
        back_populates="participant_in"
    )
    documents = relationship("Document", back_populates="case")
    tags = relationship(
        "Tag", 
        secondary=case_tags, 
        back_populates="cases"
    )
    timeline_events = relationship(
        "TimelineEvent", 
        back_populates="case"
    )
    evidence_items = relationship(
        "Evidence", 
        back_populates="case"
    )

    def __repr__(self) -> str:
        return f"<Case {self.case_number or self.title}>"


class DocumentType(str, Enum):
    """Document type enumeration."""

    PLEADING = "pleading"
    MOTION = "motion"
    BRIEF = "brief"
    AFFIDAVIT = "affidavit"
    EXHIBIT = "exhibit"
    DISCOVERY = "discovery"
    CORRESPONDENCE = "correspondence"
    COURT_ORDER = "court_order"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status enumeration."""

    DRAFT = "draft"
    FINAL = "final"
    FILED = "filed"
    SERVED = "served"
    ADMITTED = "admitted"
    REJECTED = "rejected"


class Document(Base):
    """Document model for storing case-related files and metadata."""

    __tablename__ = "documents"

    id = Column(UUIDString(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String(100), nullable=False)
    file_hash = Column(String(128), nullable=False)  # For deduplication
    document_type = Column(SQLAlchemyEnum(DocumentType), default=DocumentType.OTHER)
    status = Column(SQLAlchemyEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign keys
    case_id = Column(UUIDString(36), ForeignKey("cases.id"), nullable=False)
    uploaded_by_id = Column(UUIDString(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="documents")
    uploaded_by = relationship("User", back_populates="documents")
    related_documents = relationship(
        "Document",
        secondary=document_relationships,
        primaryjoin=id == document_relationships.c.parent_document_id,
        secondaryjoin=id == document_relationships.c.child_document_id,
        back_populates="related_documents",
    )
    evidence = relationship("Evidence", back_populates="document", uselist=False)

    def __repr__(self) -> str:
        return f"<Document {self.title} ({self.file_type})>"


class EvidenceType(str, Enum):
    """Evidence type enumeration."""

    DOCUMENT = "document"
    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    FINANCIAL_RECORD = "financial_record"
    MEDICAL_RECORD = "medical_record"
    OTHER = "other"


class EvidenceStatus(str, Enum):
    """Evidence status enumeration."""

    PENDING_REVIEW = "pending_review"
    ADMITTED = "admitted"
    EXCLUDED = "excluded"
    OBJECTED = "objected"
    SUSTAINED = "sustained"
    OVERRULED = "overruled"


class Evidence(Base):
    """Evidence model representing pieces of evidence in a case."""

    __tablename__ = "evidence"

    id = Column(UUIDString(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(SQLAlchemyEnum(EvidenceType), nullable=False)
    status = Column(
        SQLAlchemyEnum(EvidenceStatus), 
        default=EvidenceStatus.PENDING_REVIEW
    )
    exhibit_number = Column(String(50), nullable=True)
    chain_of_custody = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign keys
    case_id = Column(UUIDString(36), ForeignKey("cases.id"), nullable=False)
    document_id = Column(UUIDString(36), ForeignKey("documents.id"), nullable=True)

    # Relationships
    case = relationship("Case", back_populates="evidence_items")
    document = relationship("Document", back_populates="evidence")
    timeline_events = relationship("TimelineEvent", back_populates="evidence")

    def __repr__(self) -> str:
        return f"<Evidence {self.title} ({self.evidence_type})>"


class TimelineEventType(str, Enum):
    """Timeline event type enumeration."""

    CASE_EVENT = "case_event"
    COURT_DATE = "court_date"
    FILING = "filing"
    DISCOVERY = "discovery"
    COMMUNICATION = "communication"
    EVIDENCE_SUBMISSION = "evidence_submission"
    DEADLINE = "deadline"
    HEARING = "hearing"
    TRIAL = "trial"
    SETTLEMENT = "settlement"
    OTHER = "other"


class TimelineEvent(Base):
    """Timeline event model for case chronology."""

    __tablename__ = "timeline_events"

    id = Column(UUIDString(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(
        SQLAlchemyEnum(TimelineEventType), 
        nullable=False
    )
    event_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_important = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign keys
    case_id = Column(UUIDString(36), ForeignKey("cases.id"), nullable=False)
    created_by_id = Column(UUIDString(36), ForeignKey("users.id"), nullable=False)
    evidence_id = Column(UUIDString(36), ForeignKey("evidence.id"), nullable=True)

    # Relationships
    case = relationship("Case", back_populates="timeline_events")
    created_by = relationship("User", back_populates="events")
    evidence = relationship("Evidence", back_populates="timeline_events")

    def __repr__(self) -> str:
        return f"<TimelineEvent {self.title} ({self.event_type})>"


class Tag(Base):
    """Tag model for categorizing cases and other entities."""

    __tablename__ = "tags"

    id = Column(UUIDString(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True, index=True)
    color = Column(String(7), nullable=True)  # Hex color code
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    cases = relationship("Case", secondary=case_tags, back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"
