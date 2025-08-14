# casebuilder/models.py - Database models and API schemas

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Import the Base from our database setup
from .db.base import Base

# --- SQLAlchemy Model ---
# This defines the `evidence` table in our database
class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    description = Column(String, nullable=True)
    case_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- Pydantic Schemas ---
# These are used for API validation and response models

class EvidenceBase(BaseModel):
    filename: str
    description: Optional[str] = None
    case_id: str

class EvidenceCreate(EvidenceBase):
    pass

class EvidenceRead(EvidenceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
